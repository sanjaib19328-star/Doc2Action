import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import app

client = TestClient(app)


def test_configuration_loading():
    """Test that settings are correctly loaded with expected default or configured values."""
    assert settings.PROJECT_NAME == "Doc2Action API"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0
    assert "postgresql://" in settings.get_database_url()


def test_app_startup_and_root_endpoint():
    """Test that application starts and root endpoint returns expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert "docs" in data


def test_get_health_endpoint():
    """Test GET /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == settings.VERSION
    assert data["environment"] == settings.ENVIRONMENT


@patch("app.api.v1.endpoints.health.check_db_connection")
def test_get_db_health_endpoint_healthy(mock_check_db):
    """Test GET /api/v1/health/db endpoint when DB is reachable."""
    mock_check_db.return_value = True
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True


@patch("app.api.v1.endpoints.health.check_db_connection")
def test_get_db_health_endpoint_unhealthy(mock_check_db):
    """Test GET /api/v1/health/db endpoint when DB is unreachable."""
    mock_check_db.return_value = False
    response = client.get("/api/v1/health/db")
    assert response.status_code == 533 or response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database_connected"] is False


def test_cors_headers():
    """Test that CORS headers are present on OPTIONS preflight requests."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
