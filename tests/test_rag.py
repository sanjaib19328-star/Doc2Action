import pytest
from unittest.mock import patch
from app.modules.rag.vector_store import vector_store_instance

RAG_SPEC_YAML = """
openapi: 3.0.0
info:
  title: Payments & Refunds API
  version: 1.0.0
servers:
  - url: https://api.payments.com
paths:
  /payments/charge:
    post:
      operationId: processCharge
      summary: Charge a credit card
      description: Process a credit card payment for an order
      responses:
        '200':
          description: Charge successful
  /payments/refund:
    post:
      operationId: processRefund
      summary: Refund a transaction
      description: Issue a full or partial refund to a customer
      responses:
        '200':
          description: Refund processed
"""


def _setup_user_and_token(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login_res.json()["access_token"]


def _create_connection(client, token):
    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=RAG_SPEC_YAML):
        spec_res = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.payments.com/spec.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )
    spec_id = spec_res.json()["id"]

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={"specification_id": spec_id, "name": "Payment Gateway Connection"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return conn_res.json()["id"]


def test_rag_indexing_and_semantic_search(client):
    """Test indexing catalog endpoints into vector store and performing semantic search."""
    token = _setup_user_and_token(client, "rag1@example.com")
    conn_id = _create_connection(client, token)

    # Index connection
    idx_res = client.post(f"/api/v1/rag/index/{conn_id}", headers={"Authorization": f"Bearer {token}"})
    assert idx_res.status_code == 200
    assert idx_res.json()["indexed_count"] == 2

    # Perform semantic search for "charge card"
    search_res = client.post(
        "/api/v1/rag/search",
        json={"query": "charge card payment", "top_k": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) > 0
    assert any(r["operation_id"] == "processCharge" for r in results)


def test_rag_user_and_connection_isolation(client):
    """Test that users cannot search or index other users' connections."""
    token_a = _setup_user_and_token(client, "raga@example.com")
    token_b = _setup_user_and_token(client, "ragb@example.com")

    conn_id_a = _create_connection(client, token_a)
    conn_id_b = _create_connection(client, token_b)

    # Index User A and User B connections
    client.post(f"/api/v1/rag/index/{conn_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    client.post(f"/api/v1/rag/index/{conn_id_b}", headers={"Authorization": f"Bearer {token_b}"})

    # Search for User A -> should only receive User A results
    search_a = client.post(
        "/api/v1/rag/search",
        json={"query": "payment"},
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    for item in search_a:
        assert item["connection_id"] == conn_id_a

    # User B attempting to reindex User A's connection -> 404
    reindex_res = client.post(f"/api/v1/rag/reindex/{conn_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert reindex_res.status_code == 404


def test_rag_reindex_and_delete_index(client):
    """Test re-indexing and deleting a vector index."""
    token = _setup_user_and_token(client, "ragre@example.com")
    conn_id = _create_connection(client, token)

    # Index
    client.post(f"/api/v1/rag/index/{conn_id}", headers={"Authorization": f"Bearer {token}"})

    # Re-index
    reidx_res = client.post(f"/api/v1/rag/reindex/{conn_id}", headers={"Authorization": f"Bearer {token}"})
    assert reidx_res.status_code == 200
    assert reidx_res.json()["indexed_count"] == 2

    # Delete index
    del_res = client.delete(f"/api/v1/rag/index/{conn_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["deleted_count"] == 2

    # Search after deletion -> empty results
    search_after_del = client.post(
        "/api/v1/rag/search",
        json={"query": "payment"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search_after_del.status_code == 200
    assert len(search_after_del.json()) == 0


def test_unavailable_vector_service_handling(client):
    """Test system graceful error handling when vector service is unavailable."""
    token = _setup_user_and_token(client, "ragerr@example.com")

    # Simulate vector store downtime
    vector_store_instance.is_available = False

    try:
        search_res = client.post(
            "/api/v1/rag/search",
            json={"query": "payment"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_res.status_code == 503
        assert "unavailable" in search_res.json()["error"]["message"].lower()
    finally:
        vector_store_instance.is_available = True
