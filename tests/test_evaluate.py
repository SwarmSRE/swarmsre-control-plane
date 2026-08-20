from unittest.mock import AsyncMock

import pytest

from agents.nodes.evaluate import evaluate_node
from agents.state import IncidentState


@pytest.fixture
def mock_mcp(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr("agents.nodes.evaluate.mcp", mock)
    return mock


@pytest.mark.asyncio
async def test_evaluate_node_success(mock_mcp):
    mock_mcp.fetch_pod_status.return_value = '{"status": {"phase": "Running"}}'
    
    state: IncidentState = {
        "incident_id": "test-inc-1",
        "status": "PROPOSED",
        "raw_event": {
            "involvedObject": {
                "name": "backend-service-abc123",
                "namespace": "default"
            }
        },
        "messages": [],
    }
    
    result = await evaluate_node(state)
    
    mock_mcp.fetch_pod_status.assert_called_once_with("default", "backend-service-abc123")
    assert result["status"] == "RESOLVED"
    assert "messages" in result
    assert "Success: True" in result["messages"][0]


@pytest.mark.asyncio
async def test_evaluate_node_failure(mock_mcp):
    mock_mcp.fetch_pod_status.return_value = '{"status": {"phase": "CrashLoopBackOff"}}'
    
    state: IncidentState = {
        "incident_id": "test-inc-2",
        "status": "PROPOSED",
        "raw_event": {
            "involvedObject": {
                "name": "backend-service-xyz789",
                "namespace": "default"
            }
        },
        "messages": [],
    }
    
    result = await evaluate_node(state)
    
    mock_mcp.fetch_pod_status.assert_called_once_with("default", "backend-service-xyz789")
    assert result["status"] == "INVESTIGATING"
    assert "Success: False" in result["messages"][0]


@pytest.mark.asyncio
async def test_evaluate_node_rejected():
    state: IncidentState = {
        "incident_id": "test-inc-3",
        "status": "REJECTED",
        "messages": [],
    }
    
    result = await evaluate_node(state)
    assert "Evaluation skipped" in result["messages"][0]
