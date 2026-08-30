import pytest
import uuid
from fastapi.testclient import TestClient


def test_full_application_context_lifecycle_isolation(client: TestClient, auth_headers: dict):
    # 1. Create Application A and Application B for User 1
    app_a = client.post("/api/v1/applications", json={"name": "App Alpha", "description": "Application Alpha"}, headers=auth_headers).json()
    app_b = client.post("/api/v1/applications", json={"name": "App Beta", "description": "Application Beta"}, headers=auth_headers).json()

    app_a_id = app_a["id"]
    app_b_id = app_b["id"]

    # 2. Discover Spec and Create Connection under App A
    disc_res = client.post(
        "/api/v1/openapi/discover",
        json={"url": "https://petstore.swagger.io/v2/swagger.json", "application_id": app_a_id},
        headers=auth_headers,
    )
    spec_a_id = disc_res.json()["id"]

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={"specification_id": spec_a_id, "application_id": app_a_id, "name": "Petstore App A Connection"},
        headers=auth_headers,
    )
    conn_a_id = conn_res.json()["id"]
    endpoints_a = conn_res.json()["endpoints"]
    endpoint_a_id = None
    for ep in endpoints_a:
        if ep["path"] == "/pet/findByStatus":
            endpoint_a_id = ep["id"]
            break
    if not endpoint_a_id:
        endpoint_a_id = endpoints_a[0]["id"]

    # 3. RAG Indexing for Connection A
    index_res = client.post(f"/api/v1/rag/index/{conn_a_id}", headers=auth_headers)
    assert index_res.status_code == 200

    # 4. RAG Search: Querying with application_id = App A finds hit
    rag_a = client.post(
        "/api/v1/rag/search",
        json={"query": "find pet by status", "application_id": app_a_id},
        headers=auth_headers,
    ).json()
    assert len(rag_a) > 0
    assert rag_a[0]["application_id"] == app_a_id

    # RAG Search: Querying with application_id = App B yields ZERO hits (Cross-app RAG Isolation)
    rag_b = client.post(
        "/api/v1/rag/search",
        json={"query": "find pet by status", "application_id": app_b_id},
        headers=auth_headers,
    ).json()
    assert len(rag_b) == 0

    # 5. Proposal Creation under App A
    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_a_id,
            "application_id": app_a_id,
            "intent_summary": "Test proposal App A",
            "query_params": {"status": "available"}
        },
        headers=auth_headers
    )
    assert prop_res.status_code == 201
    prop_a_id = prop_res.json()["proposal_id"]
    assert prop_res.json()["application_id"] == app_a_id

    # Attempt to create proposal claiming App B for Endpoint A -> 400 Mismatched Application
    mismatch_prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_a_id,
            "application_id": app_b_id,
            "intent_summary": "Test mismatch proposal",
            "query_params": {"status": "available"}
        },
        headers=auth_headers
    )
    assert mismatch_prop_res.status_code == 400

    # List proposals filtered by App A vs App B
    props_a = client.get(f"/api/v1/verification/proposals?application_id={app_a_id}", headers=auth_headers).json()
    assert len(props_a) == 1
    assert props_a[0]["proposal_id"] == prop_a_id

    props_b = client.get(f"/api/v1/verification/proposals?application_id={app_b_id}", headers=auth_headers).json()
    assert len(props_b) == 0

    # 6. Proposal Execution & Execution Logs Application Tracking
    client.post(f"/api/v1/verification/proposals/{prop_a_id}/confirm", headers=auth_headers)
    exec_res = client.post(f"/api/v1/verification/proposals/{prop_a_id}/execute", headers=auth_headers)
    assert exec_res.status_code == 200

    logs_a = client.get(f"/api/v1/execution/logs?application_id={app_a_id}", headers=auth_headers).json()
    assert len(logs_a) == 1
    assert logs_a[0]["application_id"] == app_a_id

    logs_b = client.get(f"/api/v1/execution/logs?application_id={app_b_id}", headers=auth_headers).json()
    assert len(logs_b) == 0

    # 7. AI Agent Application Isolation
    # Agent with App A context finds endpoint and creates proposal or requests params under App A
    agent_a = client.post(
        "/api/v1/agent/process",
        json={"query": "Find pets by status status=available", "application_id": app_a_id},
        headers=auth_headers
    ).json()
    assert agent_a["step"] in ("WAITING_FOR_CONFIRMATION", "WAITING_FOR_INPUT")
    assert agent_a["rag_hits"][0]["application_id"] == app_a_id

    # Agent with App B context fails to find hits
    agent_b = client.post(
        "/api/v1/agent/process",
        json={"query": "Find pets with available status", "application_id": app_b_id},
        headers=auth_headers
    ).json()
    assert agent_b["step"] == "FAILED"
    assert agent_b["decision_type"] == "ERROR"
