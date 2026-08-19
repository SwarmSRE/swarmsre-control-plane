from agents.nodes.triage import triage_node


def test_triage_passes_crashloopbackoff():
    state = {
        "incident_id": "test-123",
        "status": "OPEN",
        "raw_event": {"reason": "CrashLoopBackOff"},
        "evidence": [],
        "messages": []
    }
    result = triage_node(state)
    assert result["status"] == "INVESTIGATING"

def test_triage_filters_unknown():
    state = {
        "incident_id": "test-123",
        "status": "OPEN",
        "raw_event": {"reason": "SomeUnknownEvent"},
        "evidence": [],
        "messages": []
    }
    result = triage_node(state)
    assert result["status"] == "RESOLVED"
