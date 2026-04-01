import sys
sys.path.insert(0, 'C:\\XProMetaAI')


from app.adversary import AdversaryEngine, ATTACK_SEQUENCES
from app.memory import MemoryEngine


def test_adversary_returns_query():
    a = AdversaryEngine("direct", "easy")
    q = a.get_next_query()
    assert "query" in q
    assert "risk" in q
    assert "expected" in q
    print("PASS: adversary returns query | " + q["query"][:40])


def test_all_attack_types_load():
    for attack in ["direct", "semantic_disguise", "roleplay_jailbreak",
                   "emotional_manip", "encoded"]:
        a = AdversaryEngine(attack, "expert")
        q = a.get_next_query()
        assert q["query"] != ""
        print("PASS: attack type loaded | " + attack)


def test_adversary_escalates_on_mistake():
    a = AdversaryEngine("semantic_disguise", "expert")
    q1 = a.get_next_query()
    # Simulate agent allowing when should have blocked
    q2 = a.get_next_query(last_decision="allow")
    assert q2["risk"] >= q1["risk"]
    print("PASS: adversary escalates on agent mistake")
    print("  Turn 1 risk=" + str(q1["risk"]) +
          " Turn 2 risk=" + str(q2["risk"]))


def test_adversary_tracks_errors():
    a = AdversaryEngine("roleplay_jailbreak", "hard")
    a.get_next_query()
    a.get_next_query(last_decision="allow")
    a.get_next_query(last_decision="allow")
    summary = a.get_attack_summary()
    assert summary["agent_errors"] >= 1
    print("PASS: adversary tracks agent errors | errors=" +
          str(summary["agent_errors"]))


def test_memory_escalation_detection():
    m = MemoryEngine()
    m.add_turn(1, "safe query", "allow", "safe", 0, {})
    m.add_turn(2, "risky query", "block", "risky", 3, {})
    m.add_turn(3, "dangerous query", "block", "dangerous", 4, {})
    assert m.is_escalating() is True
    assert m.detect_escalation_pattern() is True
    print("PASS: memory detects escalation pattern")
    print("  Risk trajectory: " + str(m.risk_trajectory))


def test_memory_consistency_check():
    m = MemoryEngine()
    m.add_turn(1, "q1", "block", "r1", 4, {})
    m.add_turn(2, "q2", "block", "r2", 4, {})
    m.add_turn(3, "q3", "block", "r3", 4, {})
    assert m.is_consistent() is True
    print("PASS: memory consistency check")


def test_memory_never_escalated():
    m = MemoryEngine()
    m.add_turn(1, "critical", "allow", "missed", 5, {})
    m.add_turn(2, "critical", "allow", "missed", 5, {})
    assert m.never_escalated_when_needed() is True
    print("PASS: memory detects missed escalation")


if __name__ == "__main__":
    test_adversary_returns_query()
    test_all_attack_types_load()
    test_adversary_escalates_on_mistake()
    test_adversary_tracks_errors()
    test_memory_escalation_detection()
    test_memory_consistency_check()
    test_memory_never_escalated()
    print("\nALL ADVERSARY TESTS PASSED")