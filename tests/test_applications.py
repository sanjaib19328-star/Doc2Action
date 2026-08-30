import pytest
import uuid
from fastapi.testclient import TestClient


def test_create_application_success(client: TestClient, auth_headers: dict):
    payload = {
        "name": "E-Commerce Core App",
        "description": "Main e-commerce backend service application"
    }
    response = client.post("/api/v1/applications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "owner_id" in data


def test_list_applications(client: TestClient, auth_headers: dict):
    # Create two applications
    client.post("/api/v1/applications", json={"name": "App One"}, headers=auth_headers)
    client.post("/api/v1/applications", json={"name": "App Two"}, headers=auth_headers)

    response = client.get("/api/v1/applications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_application_by_id(client: TestClient, auth_headers: dict):
    create_res = client.post("/api/v1/applications", json={"name": "Get Test App"}, headers=auth_headers)
    app_id = create_res.json()["id"]

    response = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == app_id


def test_update_application(client: TestClient, auth_headers: dict):
    create_res = client.post("/api/v1/applications", json={"name": "Original Name"}, headers=auth_headers)
    app_id = create_res.json()["id"]

    update_payload = {"name": "Updated App Name", "description": "Updated Description"}
    response = client.put(f"/api/v1/applications/{app_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated App Name"
    assert data["description"] == "Updated Description"


def test_delete_application(client: TestClient, auth_headers: dict):
    create_res = client.post("/api/v1/applications", json={"name": "App To Delete"}, headers=auth_headers)
    app_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_application_unauthenticated(client: TestClient):
    response = client.get("/api/v1/applications")
    assert response.status_code == 401


def test_application_user_isolation(client: TestClient, auth_headers: dict):
    # User 1 creates an application
    create_res = client.post("/api/v1/applications", json={"name": "User 1 App"}, headers=auth_headers)
    app_id = create_res.json()["id"]

    # Register and login User 2
    user2_reg = {"email": "user2_app_iso@doc2action.io", "password": "Password123!", "full_name": "User Two"}
    client.post("/api/v1/auth/register", json=user2_reg)
    login_res = client.post("/api/v1/auth/login", json={"email": user2_reg["email"], "password": user2_reg["password"]})
    user2_token = login_res.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # User 2 tries to read User 1's application -> 404
    get_res = client.get(f"/api/v1/applications/{app_id}", headers=user2_headers)
    assert get_res.status_code == 404

    # User 2 tries to update User 1's application -> 404
    update_res = client.put(f"/api/v1/applications/{app_id}", json={"name": "Hacked Name"}, headers=user2_headers)
    assert update_res.status_code == 404

    # User 2 tries to delete User 1's application -> 404
    delete_res = client.delete(f"/api/v1/applications/{app_id}", headers=user2_headers)
    assert delete_res.status_code == 404
