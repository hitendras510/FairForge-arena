
# ============================================================
# SafetyGuard X — Core Environment Engine
# reset() / step() / state() — full OpenEnv spec
# ============================================================

import uuid
from typing import Dict, Any, Optional, List

from app.models import (
    AgentAction, Observation, Reward, StepResult,
    ResetResult, StateResult, StateFlags, ConversationTurn
)
from app.policies import evaluate_query, get_policies_for_task
from app.memory import MemoryEngine
from app.grader import Grader
from app.tasks import get_scenario, get_turn, get_task_metadata


# ── Session Store ─────────────────────────────────────────────
_sessions: Dict[str, "Episode"] = {}


# ── Episode Class ─────────────────────────────────────────────

class Episode:
    """One full episode for a given task + scenario."""

    def __init__(self, task_id: str, scenario_index: int = 0):
        self.session_id        = str(uuid.uuid4())
        self.task_id           = task_id
        self.max_turns         = get_task_metadata(task_id)["max_turns"]
        self.turn_number       = 0
        self.done              = False
        self.cumulative_reward = 0.0

        # Load scenario
        self.scenario          = get_scenario(task_id, scenario_index)
        self.attack_type       = self.scenario.get("attack_type", "direct")

        # Engines
        self.memory            = MemoryEngine()
        self.grader            = Grader(task_id, self.max_turns)
        self.policies          = get_policies_for_task(task_id)

        # Current turn data
        self.current_turn_data: Optional[Dict[str, Any]] = None
        self._load_turn(1)

    def _load_turn(self, turn_number: int):
        """Load query for the given turn from scenario."""
        self.current_turn_data = get_turn(self.scenario, turn_number)

    def current_query(self) -> str:
        if self.current_turn_data:
            return self.current_turn_data.get("query", "")
        return ""

    def current_hint(self) -> Optional[str]:
        if self.current_turn_data:
            return self.current_turn_data.get("hint")
        return None

    def build_observation(self) -> Observation:
        """Build full Observation object for current state."""
        flags = self._build_flags()

        history = []
        for h in self.memory.get_history():
            history.append(ConversationTurn(
                turn=h["turn"],
                user_query=h["user_query"],
                agent_decision=h.get("agent_decision"),
                agent_reason=h.get("agent_reason"),
                risk_level=h.get("risk_level", 0),
                attack_type=h.get("attack_type"),
                flags=h.get("flags", {}),
            ))

        return Observation(
            task_id=self.task_id,
            turn_number=self.turn_number,
            max_turns=self.max_turns,
            current_query=self.current_query(),
            conversation_history=history,
            active_policies=self.policies,
            risk_level=self.memory.current_risk_level(),
            flags=flags,
            context_hint=self.current_hint(),
        )

    def _build_flags(self) -> StateFlags:
        """Build StateFlags from memory summary."""
        summary = self.memory.summary()
        return StateFlags(
            escalation_detected=summary.get("escalation_pattern", False),
            policy_conflict=False,
            encoded_detected=False,
            emotional_manip=False,
            roleplay_attempt=False,
            late_escalation=summary.get("escalated_too_late", False),
            over_blocking=summary.get("over_blocked", False),
            missed_escalation=summary.get("never_escalated_needed", False),
        )

    def state(self) -> StateResult:
        """Return current episode state snapshot."""
        summary = self.memory.summary()
        flags   = self._build_flags()

        history = []
        for h in self.memory.get_history():
            history.append(ConversationTurn(
                turn=h["turn"],
                user_query=h["user_query"],
                agent_decision=h.get("agent_decision"),
                agent_reason=h.get("agent_reason"),
                risk_level=h.get("risk_level", 0),
                attack_type=h.get("attack_type"),
                flags=h.get("flags", {}),
            ))

        return StateResult(
            session_id=self.session_id,
            task_id=self.task_id,
            turn_number=self.turn_number,
            max_turns=self.max_turns,
            done=self.done,
            risk_level=self.memory.current_risk_level(),
            flags=flags,
            cumulative_reward=round(self.cumulative_reward, 4),
            history=history,
            actions_taken=self.turn_number,
        )


# ── Public API ────────────────────────────────────────────────

def env_reset(task_id: str, scenario_index: int = 0) -> ResetResult:
    """Start a fresh episode."""
    if task_id not in ["easy", "medium", "hard", "expert"]:
        raise ValueError(f"Unknown task_id '{task_id}'")

    episode = Episode(task_id, scenario_index)
    _sessions[episode.session_id] = episode

    episode.turn_number = 1
    episode._load_turn(1)

    return ResetResult(
        session_id=episode.session_id,
        task_id=task_id,
        observation=episode.build_observation(),
    )


def env_step(session_id: str, action: AgentAction) -> StepResult:
    """Process one agent action."""
    episode = _get_session(session_id)

    if episode.done:
        raise ValueError("Episode already finished. Call /reset first.")

    # Evaluate current query
    query   = episode.current_query()
    history = episode.memory.get_history()

    eval_result = evaluate_query(query, episode.task_id, history)

    risk_level       = eval_result["risk_level"]
    expected         = eval_result["expected_decision"]
    triggered_rules  = eval_result["triggered_rules"]
    exceptions_apply = eval_result["exceptions_apply"]
    flags_dict       = eval_result["flags"]

    # Score this turn — FIXED: use action.decision directly (it's a string)
    turn_result = episode.grader.score_turn(
        turn=episode.turn_number,
        decision=action.decision,           # ← Fixed: no .value
        reason=action.reason,
        expected=expected,
        risk_level=risk_level,
        flags=flags_dict,
        triggered_rules=triggered_rules,
        exceptions_apply=exceptions_apply,
        memory=episode.memory,
    )

    # Update memory
    episode.memory.add_turn(
        turn=episode.turn_number,
        query=query,
        decision=action.decision,           # ← Fixed: string
        reason=action.reason,
        risk=risk_level,
        flags=flags_dict,
        attack_type=episode.attack_type,
    )

    # Step reward
    step_score = turn_result.get("step_score", 0.0)
    episode.cumulative_reward += step_score

    # Check if episode is done
    scenario_turns = len(episode.scenario.get("turns", []))
    done = (
        episode.turn_number >= episode.max_turns
        or episode.turn_number >= scenario_turns
        or action.decision == "escalate"        # ← Fixed: string comparison
    )

    # Build reward object
    if done:
        final = episode.grader.final_score(episode.memory)
        reward = Reward(
            score=final["final_score"],
            breakdown=final["breakdown"],
            feedback=final["feedback"],
            penalty=final["breakdown"].get("total_penalty", 0.0),
            bonus=final["breakdown"].get("total_bonus", 0.0),
        )
        episode.done = True
    else:
        reward = Reward(
            score=round(step_score, 4),
            breakdown={
                "correctness":       turn_result.get("correctness", 0.0),
                "policy_alignment":  turn_result.get("policy_alignment", 0.0),
                "reasoning_quality": turn_result.get("reasoning_quality", 0.0),
                "escalation":        turn_result.get("escalation_detection", 0.0),
                "step_penalty":      turn_result.get("penalty", 0.0),
                "step_bonus":        turn_result.get("bonus", 0.0),
            },
            feedback=_step_feedback(action.decision, expected, risk_level, step_score),
            penalty=turn_result.get("penalty", 0.0),
            bonus=turn_result.get("bonus", 0.0),
        )

    # Advance turn
    if not done:
        episode.turn_number += 1
        episode._load_turn(episode.turn_number)

    observation = episode.build_observation()

    return StepResult(
        observation=observation,
        reward=reward,
        done=done,
        info={
            "session_id": session_id,
            "turn": episode.turn_number,
            "expected": expected,
            "risk_level": risk_level,
            "triggered_rules": triggered_rules,
            "attack_type": episode.attack_type,
            "episode_done": done,
        },
    )


def env_state(session_id: str) -> StateResult:
    """Return current episode state."""
    episode = _get_session(session_id)
    return episode.state()


def env_grader(session_id: str) -> Dict[str, Any]:
    """Return final grader score."""
    episode = _get_session(session_id)
    result = episode.grader.final_score(episode.memory)
    return {
        "session_id": session_id,
        "task_id": episode.task_id,
        "final_score": result["final_score"],
        "breakdown": result["breakdown"],
        "feedback": result["feedback"],
        "turns_taken": episode.turn_number,
        "flags_triggered": episode._build_flags().dict(),
    }


# ── Helpers ───────────────────────────────────────────────────

def _get_session(session_id: str) -> Episode:
    if session_id not in _sessions:
        raise KeyError(f"Session '{session_id}' not found. Call /reset first.")
    return _sessions[session_id]


def _step_feedback(decision: str, expected: str, risk: int, score: float) -> str:
    if decision == expected:
        return f"Correct decision '{decision}' | risk={risk} | score={score:.2f}"
    return f"Decision '{decision}' vs expected '{expected}' | risk={risk} | score={score:.2f}"