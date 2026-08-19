import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_create_and_get_incident():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create incident
        response = await ac.post(
            "/api/incidents",
            json={
                "title": "Test Pod Crash",
                "description": "Pod is crashlooping",
                "source": "kubernetes-watcher",
                "raw_event": {"reason": "CrashLoopBackOff"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Pod Crash"
        assert data["status"] == "OPEN"
        incident_id = data["id"]
        
        # Get incident
        get_response = await ac.get(f"/api/incidents/{incident_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == incident_id

@pytest.mark.asyncio
async def test_get_nonexistent_incident():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/incidents/fake-id")
        assert response.status_code == 404
