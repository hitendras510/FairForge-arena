import sys
sys.path.insert(0, 'C:\\XProMetaAI')

from app.models import (
    AgentAction, Decision, PolicyRule,
    StateFlags, ConversationTurn, Observation,
    Reward, StepResult, ResetResult, StateResult
)


def test_agent_action_valid():
    a = AgentAction(
        decision=Decision.BLOCK,
        reason="violates policy P001 harmful content",
        modified_response=None,
        confidence=0.9,
    )
    assert a.decision == Decision.BLOCK
    assert len(a.reason) >= 10
    print("PASS: agent action valid")


def test_agent_action_all_decisions():
    for d in ["allow", "block", "modify", "escalate", "clarify"]:
        a = AgentAction(
            decision=d,
            reason="test reason for policy check",
            modified_response="safe version" if d == "modify" else None,
            confidence=0.8,
        )
        assert a.decision == d
    print("PASS: all decisions valid")


def test_policy_rule():
    rule = PolicyRule(
        rule_id="P001",
        description="Block harmful content",
        block_keywords=["bomb", "weapon"],
        allow_exceptions=["educational"],
        requires_escalation=True,
        requires_clarification=False,
    )
    assert rule.rule_id == "P001"
    assert "bomb" in rule.block_keywords
    print("PASS: policy rule valid")


def test_state_flags_default():
    flags = StateFlags(
        escalation_detected=False,
        policy_conflict=False,
        encoded_detected=False,
        emotional_manip=False,
        roleplay_attempt=False,
        late_escalation=False,
        over_blocking=False,
        missed_escalation=False,
    )
    assert flags.escalation_detected == False
    print("PASS: state flags default")


def test_reward_range():
    r = Reward(
        score=0.85,
        breakdown={"correctness": 0.9, "policy_alignment": 0.8},
        feedback="Good performance",
        penalty=0.0,
        bonus=0.05,
    )
    assert 0.0 <= r.score <= 1.0
    print("PASS: reward range valid")


if __name__ == "__main__":
    test_agent_action_valid()
    test_agent_action_all_decisions()
    test_policy_rule()
    test_state_flags_default()
    test_reward_range()
    print("\nALL MODEL TESTS PASSED")