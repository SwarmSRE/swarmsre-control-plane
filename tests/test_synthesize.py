import pytest
from langchain_core.runnables import RunnableLambda

from agents.nodes.synthesize import RCASummary, synthesize_node
from agents.state import IncidentState


@pytest.fixture
def mock_get_orchestrator_llm(monkeypatch):
    def fake_llm_invoke(inputs):
        return RCASummary(
            rca_summary="Memory saturation caused OOMKilled",
            confidence_score=0.9,
            proposed_patch="apiVersion: v1\nkind: Pod"
        )
        
    class MockLLM:
        def with_structured_output(self, schema):
            return RunnableLambda(fake_llm_invoke)

    monkeypatch.setattr("agents.nodes.synthesize.get_orchestrator_llm", lambda: MockLLM())


@pytest.mark.asyncio
async def test_synthesize_node(mock_get_orchestrator_llm):
    state: IncidentState = {
        "incident_id": "test-inc-1",
        "status": "INVESTIGATING",
        "raw_event": {"reason": "OOMKilled"},
        "log_hunter_output": {"error_class": "OOMKilled"},
        "telemetry_output": {"resource_status": "memory_saturation"},
        "evidence": [],
        "messages": [],
        "confidence_score": 0.0
    }
    
    result = await synthesize_node(state)
    
    assert "rca_summary" in result
    assert result["rca_summary"] == "Memory saturation caused OOMKilled"
    assert result["confidence_score"] == 0.9
    assert "messages" in result
    assert "[Supervisor]" in result["messages"][0]


@pytest.mark.asyncio
async def test_synthesize_no_findings(mock_get_orchestrator_llm):
    state: IncidentState = {
        "incident_id": "test-inc-2",
        "status": "INVESTIGATING",
        "raw_event": {},
        "evidence": [],
        "messages": [],
        "confidence_score": 0.0
    }
    
    result = await synthesize_node(state)
    assert result["rca_summary"] == "Memory saturation caused OOMKilled"
    assert result["confidence_score"] == 0.9
    assert "[Supervisor]" in result["messages"][0]
