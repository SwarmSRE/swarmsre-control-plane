import pytest
from langchain_core.runnables import RunnableLambda

from agents.nodes.telemetry_analyst import TelemetryOutput, telemetry_analyst_node
from agents.state import IncidentState


@pytest.fixture
def mock_get_worker_llm(monkeypatch):
    def fake_llm_invoke(inputs):
        return TelemetryOutput(
            resource_status="memory_saturation",
            saturation_signals=["MEMORY: 1024Mi (near limit)"],
            anomalies=[]
        )
        
    class MockLLM:
        def with_structured_output(self, schema):
            return RunnableLambda(fake_llm_invoke)

    monkeypatch.setattr("agents.nodes.telemetry_analyst.get_worker_llm", lambda: MockLLM())


@pytest.fixture
def mock_mcp(monkeypatch):
    class MockMCP:
        async def fetch_pod_top(self, namespace, pod_name):
            return "NAME                          CPU(cores)   MEMORY(bytes)\nbackend-service-abc123        1500m        1024Mi"
            
        async def fetch_pod_status(self, namespace, pod_name):
            return '{"status": {"phase": "Running", "containerStatuses": [{"restartCount": 5}]}}'
            
    monkeypatch.setattr("agents.nodes.telemetry_analyst.mcp", MockMCP())


@pytest.mark.asyncio
async def test_telemetry_analyst_node(mock_get_worker_llm, mock_mcp):
    state: IncidentState = {
        "incident_id": "test-inc-1",
        "status": "INVESTIGATING",
        "raw_event": {
            "reason": "OOMKilled",
            "involved_object": {
                "namespace": "default",
                "name": "backend-service-abc123"
            }
        },
        "evidence": [
            {
                "source": "investigation",
                "events": "Warning OOMKilling pod/backend-service-abc123"
            }
        ],
        "messages": [],
        "confidence_score": 0.0
    }
    
    result = await telemetry_analyst_node(state)
    
    assert "telemetry_output" in result
    output = result["telemetry_output"]
    assert output["resource_status"] == "memory_saturation"
    assert "messages" in result
    assert "Telemetry Analyst identified resource status: memory_saturation" in result["messages"][0]


@pytest.mark.asyncio
async def test_telemetry_analyst_no_pod_name():
    state: IncidentState = {
        "incident_id": "test-inc-2",
        "status": "INVESTIGATING",
        "raw_event": {},
        "evidence": [],
        "messages": [],
        "confidence_score": 0.0
    }
    
    with pytest.raises(ValueError, match="no pod name in event"):
        await telemetry_analyst_node(state)
