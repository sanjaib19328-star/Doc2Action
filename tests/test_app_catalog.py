import pytest
import uuid
from fastapi.testclient import TestClient


def test_application_scoped_discovery_and_catalog_isolation(client: TestClient, auth_headers: dict):
    # 1. User creates Application A and Application B
    app_a_res = client.post("/api/v1/applications", json={"name": "Application A"}, headers=auth_headers)
    app_a_id = app_a_res.json()["id"]

    app_b_res = client.post("/api/v1/applications", json={"name": "Application B"}, headers=auth_headers)
    app_b_id = app_b_res.json()["id"]

    # 2. Discover Spec under Application A
    disc_payload = {
        "url": "https://petstore.swagger.io/v2/swagger.json",
        "application_id": app_a_id
    }
    disc_res = client.post("/api/v1/openapi/discover", json=disc_payload, headers=auth_headers)
    assert disc_res.status_code == 201
    spec_a_id = disc_res.json()["id"]
    assert disc_res.json()["application_id"] == app_a_id

    # 3. List specifications filtered by Application A vs Application B
    list_app_a = client.get(f"/api/v1/openapi/specifications?application_id={app_a_id}", headers=auth_headers).json()
    assert len(list_app_a) == 1
    assert list_app_a[0]["id"] == spec_a_id

    list_app_b = client.get(f"/api/v1/openapi/specifications?application_id={app_b_id}", headers=auth_headers).json()
    assert len(list_app_b) == 0

    # 4. Attempt to create connection for Application B using Spec A (Mismatched App -> 400 Bad Request)
    mismatch_payload = {
        "specification_id": spec_a_id,
        "application_id": app_b_id,
        "name": "Mismatched Connection"
    }
    mismatch_res = client.post("/api/v1/catalog/connections", json=mismatch_payload, headers=auth_headers)
    assert mismatch_res.status_code == 400
    assert "Mismatched application" in mismatch_res.json()["error"]["message"]

    # 5. Create connection for Application A using Spec A -> 201
    valid_conn_payload = {
        "specification_id": spec_a_id,
        "application_id": app_a_id,
        "name": "App A Connection"
    }
    conn_res = client.post("/api/v1/catalog/connections", json=valid_conn_payload, headers=auth_headers)
    assert conn_res.status_code == 201
    conn_a_id = conn_res.json()["id"]
    assert conn_res.json()["application_id"] == app_a_id

    # 6. List connections filtered by Application A vs Application B
    conns_a = client.get(f"/api/v1/catalog/connections?application_id={app_a_id}", headers=auth_headers).json()
    assert len(conns_a) == 1
    assert conns_a[0]["id"] == conn_a_id

    conns_b = client.get(f"/api/v1/catalog/connections?application_id={app_b_id}", headers=auth_headers).json()
    assert len(conns_b) == 0

    # 7. Nonexistent / invalid application ID handling
    fake_app_id = str(uuid.uuid4())
    fake_disc_res = client.post("/api/v1/openapi/discover", json={"url": "https://petstore.swagger.io/v2/swagger.json", "application_id": fake_app_id}, headers=auth_headers)
    assert fake_disc_res.status_code == 404

    # 8. User 2 isolation: User 2 cannot discover under User 1's Application A
    user2_reg = {"email": "app_catalog_user2@doc2action.io", "password": "Password123!", "full_name": "User 2"}
    client.post("/api/v1/auth/register", json=user2_reg)
    login_user2 = client.post("/api/v1/auth/login", json={"email": user2_reg["email"], "password": user2_reg["password"]})
    user2_headers = {"Authorization": f"Bearer {login_user2.json()['access_token']}"}

    u2_disc_res = client.post("/api/v1/openapi/discover", json={"url": "https://petstore.swagger.io/v2/swagger.json", "application_id": app_a_id}, headers=user2_headers)
    assert u2_disc_res.status_code == 404
