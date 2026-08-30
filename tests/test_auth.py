import pytest
from app.core.security import verify_password, decode_access_token


def test_user_registration(client):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "testuser@example.com", "password": "securepassword123", "full_name": "Test User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_duplicate_registration_fails(client):
    """Test that registering an existing email returns 400."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "securepassword123"},
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "anotherpassword123"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["error"]["message"]


def test_valid_login_json(client):
    """Test valid login via JSON body."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "mysecretpassword"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "mysecretpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_valid_login_form_swagger(client):
    """Test valid login via OAuth2 form data (Swagger compatibility)."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "swagger@example.com", "password": "mysecretpassword"},
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "swagger@example.com", "password": "mysecretpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    """Test login with incorrect password returns 401."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "correctpassword"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with non-existent user returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"},
    )
    assert response.status_code == 401


def test_jwt_validation_and_protected_me_endpoint(client):
    """Test accessing protected /me endpoint with valid JWT Bearer token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "mysecretpassword", "full_name": "Me User"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "mysecretpassword"},
    )
    token = login_res.json()["access_token"]

    # Verify token payload
    payload = decode_access_token(token)
    assert payload is not None
    assert "sub" in payload

    # Access protected route
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"


def test_protected_endpoint_without_token_fails(client):
    """Test accessing protected route without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token_fails(client):
    """Test accessing protected route with invalid token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


def test_inactive_user_cannot_access_protected_route(client, db):
    """Test that inactive users are blocked from logging in or accessing protected routes."""
    # Register user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": "inactive@example.com", "password": "mysecretpassword"},
    )
    user_id = reg_res.json()["id"]

    # Log in to get token before deactivation
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "mysecretpassword"},
    )
    token = login_res.json()["access_token"]

    # Deactivate user directly in DB
    from app.modules.auth.models import User
    user = db.query(User).filter(User.email == "inactive@example.com").first()
    user.is_active = False
    db.commit()

    # Attempt login when inactive
    login_attempt = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "mysecretpassword"},
    )
    assert login_attempt.status_code == 400
    assert "Inactive user account" in login_attempt.json()["error"]["message"]

    # Attempt to access /me with token when inactive
    me_attempt = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_attempt.status_code == 400
    assert "Inactive user account" in me_attempt.json()["error"]["message"]


def test_authentication_consistency_json_and_form(client):
    """
    Test authentication consistency between JSON (/login) and Form (/token) endpoints.
    Both should return valid tokens for the exact same credentials that unlock /me.
    """
    client.post(
        "/api/v1/auth/register",
        json={"email": "consistent@example.com", "password": "samepassword123"},
    )

    # Token via JSON
    res_json = client.post(
        "/api/v1/auth/login",
        json={"email": "consistent@example.com", "password": "samepassword123"},
    )
    token_json = res_json.json()["access_token"]

    # Token via Form
    res_form = client.post(
        "/api/v1/auth/token",
        data={"username": "consistent@example.com", "password": "samepassword123"},
    )
    token_form = res_form.json()["access_token"]

    # Both tokens must succeed on protected endpoint
    me_json = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_json}"})
    me_form = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_form}"})

    assert me_json.status_code == 200
    assert me_form.status_code == 200
    assert me_json.json()["email"] == me_form.json()["email"] == "consistent@example.com"
