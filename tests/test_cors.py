from fastapi.testclient import TestClient


def test_cors_preflight_localhost(client: TestClient):
    """Test CORS OPTIONS preflight request from localhost."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_preflight_vercel_origin(client: TestClient):
    """Test CORS OPTIONS preflight request from Vercel deployment."""
    headers = {
        "Origin": "https://doc2action.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://doc2action.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_vercel_preview_subdomain(client: TestClient):
    """Test CORS OPTIONS preflight request from dynamic Vercel preview domain."""
    headers = {
        "Origin": "https://doc2action-git-main-sanjaib19328-star.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://doc2action-git-main-sanjaib19328-star.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin_rejected(client: TestClient):
    """Test that unauthorized origin is not granted Access-Control-Allow-Origin header."""
    headers = {
        "Origin": "https://malicious-site.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.headers.get("access-control-allow-origin") is None
