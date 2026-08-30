import pytest
from fastapi.testclient import TestClient

def test_agent_unauthenticated(client: TestClient):
    response = client.post("/api/v1/agent/process", json={"query": "Find pets with available status"})
    assert response.status_code == 401

def test_agent_authenticated_process_flow(client: TestClient, auth_headers: dict):
    # 1. Discover spec
    res = client.post(
        "/api/v1/openapi/discover",
        json={"url": "https://petstore.swagger.io/v2/swagger.json"},
        headers=auth_headers
    )
    assert res.status_code == 201
    spec_id = res.json()["id"]

    # 2. Create catalog connection
    res = client.post(
        "/api/v1/catalog/connections",
        json={"specification_id": spec_id, "name": "Agent Test Connection", "auth_config": {"type": "none"}},
        headers=auth_headers
    )
    assert res.status_code == 201
    conn_id = res.json()["id"]

    # 3. Index connection in RAG
    res = client.post(f"/api/v1/rag/index/{conn_id}", headers=auth_headers)
    assert res.status_code == 200

    # 4. Process user query via Agent
    agent_res = client.post(
        "/api/v1/agent/process",
        json={"query": "Find pets with status=available", "connection_id": conn_id},
        headers=auth_headers
    )
    assert agent_res.status_code == 200
    data = agent_res.json()
    assert data["step"] in ["WAITING_FOR_CONFIRMATION", "WAITING_FOR_INPUT"]
    assert data["decision_type"] in ["WAIT_FOR_CONFIRMATION", "REQUEST_PARAMETERS"]

    if data["step"] == "WAITING_FOR_CONFIRMATION":
        proposal_id = data["proposal"]["proposal_id"]
        # Confirm Proposal
        confirm_res = client.post(f"/api/v1/verification/proposals/{proposal_id}/confirm", headers=auth_headers)
        assert confirm_res.status_code == 200
        assert confirm_res.json()["status"] == "confirmed"
