
import pytest
from langchain_core.runnables import RunnableLambda

from agents.nodes.log_hunter import LogHunterOutput, log_hunter_node
from agents.state import IncidentState


@pytest.fixture
def mock_get_worker_llm(monkeypatch):
    def fake_llm_invoke(inputs):
        return LogHunterOutput(
            error_class="CrashLoopBackOff",
            stack_trace="Traceback (most recent call last):\n  File 'app.py', line 10...",
            frequency="constant",
            first_seen="2026-08-20T10:00:00Z"
        )
        
    class MockLLM:
        def with_structured_output(self, schema):
            return RunnableLambda(fake_llm_invoke)

    monkeypatch.setattr("agents.nodes.log_hunter.get_worker_llm", lambda: MockLLM())

@pytest.mark.asyncio
async def test_log_hunter_node(mock_get_worker_llm):
    state: IncidentState = {
        "incident_id": "test-inc-1",
        "status": "INVESTIGATING",
        "raw_event": {"reason": "CrashLoopBackOff"},
        "evidence": [
            {
                "source": "investigation",
                "logs": "Traceback (most recent call last):\n  File 'app.py', line 10...",
                "events": "Back-off restarting failed container"
            }
        ],
        "messages": [],
        "confidence_score": 0.0
    }
    
    result = await log_hunter_node(state)
    
    assert "log_hunter_output" in result
    output = result["log_hunter_output"]
    assert output["error_class"] == "CrashLoopBackOff"
    assert output["frequency"] == "constant"
    assert output["stack_trace"] is not None
    assert "messages" in result
    assert "Log Hunter identified error class: CrashLoopBackOff" in result["messages"][0]

@pytest.mark.asyncio
async def test_log_hunter_no_evidence():
    state: IncidentState = {
        "incident_id": "test-inc-2",
        "status": "INVESTIGATING",
        "raw_event": {},
        "evidence": [],
        "messages": [],
        "confidence_score": 0.0
    }
    
    result = await log_hunter_node(state)
    assert "log_hunter_output" not in result
    assert "Log Hunter skipped" in result["messages"][0]
