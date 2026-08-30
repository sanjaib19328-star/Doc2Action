import pytest
from unittest.mock import patch

VALID_SPEC_YAML = """
openapi: 3.0.0
info:
  title: Test Catalog API
  version: 1.2.3
servers:
  - url: https://catalog.example.com/api
paths:
  /items:
    get:
      operationId: getItems
      summary: Get all items
      responses:
        '200':
          description: OK
    post:
      operationId: createItem
      summary: Create item
      responses:
        '201':
          description: Created
"""


def _setup_user_and_token(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login_res.json()["access_token"]


def _discover_spec(client, token):
    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=VALID_SPEC_YAML):
        res = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://catalog.example.com/spec.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )
    return res.json()["id"]


def test_create_connection_and_endpoint_extraction(client):
    """Test creating an API connection from a discovered spec extracts catalog endpoints."""
    token = _setup_user_and_token(client, "cat1@example.com")
    spec_id = _discover_spec(client, token)

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={
            "specification_id": spec_id,
            "name": "Custom Catalog Connection",
            "auth_config": {"type": "bearer", "token": "testtoken"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conn_res.status_code == 201
    data = conn_res.json()
    assert data["name"] == "Custom Catalog Connection"
    assert data["base_url"] == "https://catalog.example.com/api"
    assert len(data["endpoints"]) == 2

    # Check endpoints list
    op_ids = [ep["operation_id"] for ep in data["endpoints"]]
    assert "getItems" in op_ids
    assert "createItem" in op_ids


def test_list_and_get_connection_endpoints(client):
    """Test listing user connections and getting connection endpoints."""
    token = _setup_user_and_token(client, "cat2@example.com")
    spec_id = _discover_spec(client, token)

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={"specification_id": spec_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    conn_id = conn_res.json()["id"]

    # List connections
    list_res = client.get("/api/v1/catalog/connections", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == conn_id

    # Get endpoints endpoint
    ep_res = client.get(f"/api/v1/catalog/connections/{conn_id}/endpoints", headers={"Authorization": f"Bearer {token}"})
    assert ep_res.status_code == 200
    assert len(ep_res.json()) == 2


def test_delete_connection(client):
    """Test deleting an API connection removes connection and its endpoints."""
    token = _setup_user_and_token(client, "cat3@example.com")
    spec_id = _discover_spec(client, token)

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={"specification_id": spec_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    conn_id = conn_res.json()["id"]

    del_res = client.delete(f"/api/v1/catalog/connections/{conn_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200

    # Ensure connection is gone
    get_res = client.get(f"/api/v1/catalog/connections/{conn_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.status_code == 404


def test_strict_user_isolation_for_connections_and_endpoints(client):
    """Test User A cannot access or delete User B's connections or endpoints."""
    token_a = _setup_user_and_token(client, "usera@example.com")
    token_b = _setup_user_and_token(client, "userb@example.com")

    spec_id_a = _discover_spec(client, token_a)

    conn_a = client.post(
        "/api/v1/catalog/connections",
        json={"specification_id": spec_id_a},
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    conn_id_a = conn_a["id"]

    # User B attempts to view User A's connection details -> 404
    get_b = client.get(f"/api/v1/catalog/connections/{conn_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_b.status_code == 404

    # User B attempts to view User A's endpoints -> 404
    ep_b = client.get(f"/api/v1/catalog/connections/{conn_id_a}/endpoints", headers={"Authorization": f"Bearer {token_b}"})
    assert ep_b.status_code == 404

    # User B attempts to delete User A's connection -> 404
    del_b = client.delete(f"/api/v1/catalog/connections/{conn_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 404

    # User A's connection must still exist untouched
    get_a = client.get(f"/api/v1/catalog/connections/{conn_id_a}", headers={"Authorization": f"Bearer {token_a}"})
    assert get_a.status_code == 200
