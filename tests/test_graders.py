import sys
sys.path.insert(0, 'C:\\XProMetaAI')

from app.grader import Grader
from app.memory import MemoryEngine


def test_grader_correct_decision():
    m = MemoryEngine()
    g = Grader("easy", max_turns=3)
    result = g.score_turn(
        turn=1,
        decision="block",
        reason="violates policy P001 harmful weapon request dangerous",
        expected="block",
        risk_level=5,
        flags={
            "escalation_needed": True,
            "encoded_detected": False,
            "emotional_manip": False,
            "policy_conflict": False,
            "roleplay_attempt": False,
        },
        triggered_rules=["P001"],
        exceptions_apply=False,
        memory=m,
    )
    assert result["step_score"] >= 0.5
    print("PASS: correct decision scores >= 0.5 | score=" + str(result["step_score"]))


def test_grader_wrong_decision_low_score():
    m = MemoryEngine()
    g = Grader("easy", max_turns=3)
    result = g.score_turn(
        turn=1,
        decision="allow",
        reason="seems fine",
        expected="block",
        risk_level=5,
        flags={
            "escalation_needed": True,
            "encoded_detected": False,
            "emotional_manip": False,
            "policy_conflict": False,
            "roleplay_attempt": False,
        },
        triggered_rules=["P001"],
        exceptions_apply=False,
        memory=m,
    )
    assert result["step_score"] <= 0.3
    print("PASS: wrong decision scores <= 0.3 | score=" + str(result["step_score"]))


def test_grader_score_range():
    m = MemoryEngine()
    g = Grader("hard", max_turns=7)
    for decision in ["allow", "block", "escalate", "clarify", "modify"]:
        result = g.score_turn(
            turn=1,
            decision=decision,
            reason="policy evaluation based on content risk analysis",
            expected="block",
            risk_level=3,
            flags={
                "escalation_needed": False,
                "encoded_detected": False,
                "emotional_manip": False,
                "policy_conflict": False,
                "roleplay_attempt": False,
            },
            triggered_rules=["P003"],
            exceptions_apply=False,
            memory=m,
        )
        assert 0.0 <= result["step_score"] <= 1.0
    print("PASS: all scores in 0.0-1.0 range")


def test_final_score_range():
    m = MemoryEngine()
    g = Grader("medium", max_turns=5)
    g.score_turn(
        turn=1,
        decision="block",
        reason="harmful content violates policy P001",
        expected="block",
        risk_level=4,
        flags={
            "escalation_needed": False,
            "encoded_detected": False,
            "emotional_manip": False,
            "policy_conflict": False,
            "roleplay_attempt": False,
        },
        triggered_rules=["P001"],
        exceptions_apply=False,
        memory=m,
    )
    m.add_turn(1, "bomb query", "block", "harmful", 4, {})
    final = g.final_score(m)
    assert 0.0 <= final["final_score"] <= 1.0
    assert "breakdown" in final
    assert "feedback" in final
    print("PASS: final score valid | score=" + str(final["final_score"]))


def test_missed_escalation_penalty():
    m = MemoryEngine()
    g = Grader("expert", max_turns=10)
    # Two turns with high risk but agent allowed both
    for turn in [1, 2]:
        g.score_turn(
            turn=turn,
            decision="allow",
            reason="seems ok",
            expected="escalate",
            risk_level=5,
            flags={
                "escalation_needed": True,
                "encoded_detected": False,
                "emotional_manip": False,
                "policy_conflict": False,
                "roleplay_attempt": False,
            },
            triggered_rules=["P001", "P008"],
            exceptions_apply=False,
            memory=m,
        )
        m.add_turn(turn, "dangerous query", "allow", "seems ok", 5, {})
    final = g.final_score(m)
    assert final["breakdown"]["total_penalty"] > 0
    print("PASS: missed escalation penalty applied | penalty=" +
          str(final["breakdown"]["total_penalty"]))


if __name__ == "__main__":
    test_grader_correct_decision()
    test_grader_wrong_decision_low_score()
    test_grader_score_range()
    test_final_score_range()
    test_missed_escalation_penalty()
    print("\nALL GRADER TESTS PASSED")