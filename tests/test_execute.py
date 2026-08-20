from unittest.mock import AsyncMock

import pytest

from agents.nodes.execute import execute_node
from agents.state import IncidentState


@pytest.fixture
def mock_mcp(monkeypatch):
    mock = AsyncMock()
    mock.apply_patch.return_value = "pod/backend-service-abc123 patched"
    monkeypatch.setattr("agents.nodes.execute.mcp", mock)
    return mock


@pytest.mark.asyncio
async def test_execute_node(mock_mcp):
    state: IncidentState = {
        "incident_id": "test-inc-1",
        "status": "PROPOSED",
        "proposed_patch": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: backend-service-abc123",
        "messages": [],
    }
    
    result = await execute_node(state)
    
    mock_mcp.apply_patch.assert_called_once_with("apiVersion: v1\nkind: Pod\nmetadata:\n  name: backend-service-abc123")
    assert "messages" in result
    assert "Execution complete" in result["messages"][0]


@pytest.mark.asyncio
async def test_execute_node_rejected():
    state: IncidentState = {
        "incident_id": "test-inc-2",
        "status": "REJECTED",
        "proposed_patch": "apiVersion: v1\nkind: Pod\nmetadata:\n  name: backend-service-abc123",
        "messages": [],
    }
    
    result = await execute_node(state)
    assert "Execution skipped" in result["messages"][0]
