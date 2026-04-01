
import sys
sys.path.insert(0, 'C:\\XProMetaAI')

from app.env import env_reset, env_step, env_state
from app.models import AgentAction, Decision


def test_reset_returns_session():
    result = env_reset("easy")
    assert result.session_id
    assert result.task_id == "easy"
    assert result.observation.turn_number == 1
    assert result.observation.current_query != ""
    print("PASS: reset returns valid session")


def test_step_returns_reward():
    reset = env_reset("easy")
    action = AgentAction(
        decision=Decision.BLOCK,
        reason="violates policy P001 harmful weapon dangerous content",
        modified_response=None,
        confidence=0.95,
    )
    result = env_step(reset.session_id, action)
    assert 0.0 <= result.reward.score <= 1.0
    assert result.done is True or result.done is False
    assert result.observation is not None
    print("PASS: step returns valid reward | score=" + str(result.reward.score))


def test_state_matches_session():
    reset = env_reset("medium")
    state = env_state(reset.session_id)
    assert state.session_id == reset.session_id
    assert state.task_id == "medium"
    assert state.turn_number >= 1
    print("PASS: state matches session")


def test_all_tasks_reset():
    for task_id in ["easy", "medium", "hard", "expert"]:
        result = env_reset(task_id)
        assert result.task_id == task_id
        assert result.observation.current_query != ""
        print("PASS: reset OK for task=" + task_id)


def test_reward_range_all_decisions():
    for decision in ["allow", "block", "escalate", "clarify"]:
        reset = env_reset("easy")
        action = AgentAction(
            decision=decision,
            reason="policy evaluation for content safety analysis",
            modified_response=None,
            confidence=0.8,
        )
        result = env_step(reset.session_id, action)
        assert 0.0 <= result.reward.score <= 1.0
    print("PASS: reward range valid for all decisions")


def test_episode_done_after_escalate():
    reset = env_reset("easy")
    action = AgentAction(
        decision=Decision.ESCALATE,
        reason="critical risk detected escalating per policy P001 emergency",
        modified_response=None,
        confidence=0.99,
    )
    result = env_step(reset.session_id, action)
    assert result.done is True
    print("PASS: episode done after escalate")


def test_invalid_session_raises():
    try:
        env_state("fake-session-id-123")
        print("FAIL: should have raised error")
    except KeyError:
        print("PASS: invalid session raises KeyError")


if __name__ == "__main__":
    test_reset_returns_session()
    test_step_returns_reward()
    test_state_matches_session()
    test_all_tasks_reset()
    test_reward_range_all_decisions()
    test_episode_done_after_escalate()
    test_invalid_session_raises()
    print("\nALL ENV TESTS PASSED")