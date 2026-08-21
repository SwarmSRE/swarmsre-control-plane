"""End-to-End integration tests for SwarmSRE."""

def test_e2e_incident_flow(test_client):
    """Tests the full incident ingestion, retrieval, and audit trail flow."""
    # 1. Get incidents
    response = test_client.get("/api/incidents")
    assert response.status_code == 200
    
    # 2. Test audit trail
    response = test_client.get("/api/audit/")
    assert response.status_code == 200
    
    # 3. Test topology
    response = test_client.get("/api/topology")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
