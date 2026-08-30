import pytest
from unittest.mock import patch
from app.modules.openapi.ssrf import validate_url_against_ssrf, SSRFVulnerabilityException
from app.modules.openapi.service import discover_and_store_spec

VALID_OPENAPI3_YAML = """
openapi: 3.0.1
info:
  title: Sample Pet Store API
  description: A sample API for testing OpenAPI 3.x parser
  version: 1.0.0
servers:
  - url: https://api.petstore.com/v1
    description: Production server
paths:
  /pets:
    get:
      operationId: listPets
      summary: List all pets
      description: Returns a list of pets
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: A paged array of pets
    post:
      operationId: createPet
      summary: Create a pet
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: Null response
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-KEY
"""

VALID_SWAGGER2_JSON = """
{
  "swagger": "2.0",
  "info": {
    "title": "Swagger Sample API",
    "version": "2.0.0",
    "description": "Sample Swagger 2.0 spec"
  },
  "host": "api.swagger.com",
  "basePath": "/v2",
  "schemes": ["https"],
  "paths": {
    "/users": {
      "get": {
        "operationId": "getUsers",
        "summary": "Get users",
        "responses": {
          "200": { "description": "Success" }
        }
      }
    }
  },
  "securityDefinitions": {
    "BearerAuth": {
      "type": "apiKey",
      "name": "Authorization",
      "in": "header"
    }
  }
}
"""


def test_ssrf_protection_blocks_localhost_and_private_ips():
    """Test that SSRF validator blocks localhost, loopback, and private IP addresses."""
    restricted_urls = [
        "http://localhost/openapi.json",
        "http://127.0.0.1:8000/spec.json",
        "http://0.0.0.0/spec.yaml",
        "http://192.168.1.1/api-docs",
        "http://10.0.0.1/swagger.json",
        "http://172.16.0.1/spec.json",
        "ftp://example.com/spec.json",  # non-http
    ]
    for url in restricted_urls:
        with pytest.raises(SSRFVulnerabilityException):
            validate_url_against_ssrf(url)


def test_ssrf_allows_public_https_url():
    """Test that SSRF validator passes valid public http/https URLs."""
    valid_url = "https://petstore.swagger.io/v2/swagger.json"
    result = validate_url_against_ssrf(valid_url)
    assert result == valid_url


def test_missing_url_returns_400(client):
    """Test discovering spec with missing or empty URL returns 400."""
    # Register and log in
    client.post("/api/v1/auth/register", json={"email": "spec1@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "spec1@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    response = client.post(
        "/api/v1/openapi/discover",
        json={"url": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_discover_valid_openapi_3_yaml(client, db):
    """Test discovering and parsing valid OpenAPI 3.0 YAML spec."""
    client.post("/api/v1/auth/register", json={"email": "spec2@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "spec2@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=VALID_OPENAPI3_YAML):
        response = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.example.com/openapi.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Sample Pet Store API"
    assert data["version"] == "1.0.0"
    assert data["spec_version"] == "3.0.1"
    assert data["base_url"] == "https://api.petstore.com/v1"
    assert len(data["operations"]) == 2
    assert len(data["security_schemes"]) == 1
    assert data["security_schemes"][0]["scheme_name"] == "ApiKeyAuth"


def test_discover_valid_swagger_2_json(client):
    """Test discovering and parsing valid Swagger 2.0 JSON spec."""
    client.post("/api/v1/auth/register", json={"email": "spec3@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "spec3@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=VALID_SWAGGER2_JSON):
        response = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.example.com/swagger.json"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Swagger Sample API"
    assert data["spec_version"] == "2.0"
    assert data["base_url"] == "https://api.swagger.com/v2"
    assert len(data["operations"]) == 1
    assert data["operations"][0]["operation_id"] == "getUsers"


def test_discover_malformed_json_fails(client):
    """Test that malformed JSON returns 400 invalid spec error."""
    client.post("/api/v1/auth/register", json={"email": "spec4@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "spec4@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    bad_json = "{\"openapi\": \"3.0.0\", \"info\": { unclosed json }"

    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=bad_json):
        response = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.example.com/bad.json"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert "Malformed JSON" in response.json()["error"]["message"]


def test_discover_invalid_specification_structure_fails(client):
    """Test that missing required fields (e.g. info or title) returns 400 error."""
    client.post("/api/v1/auth/register", json={"email": "spec5@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "spec5@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    invalid_spec = "openapi: 3.0.0\ninfo:\n  description: missing title"

    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=invalid_spec):
        response = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.example.com/invalid.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert "missing required 'title'" in response.json()["error"]["message"]


def test_get_discovered_specifications_and_details(client):
    """Test listing and fetching detailed discovered specification by ID."""
    client.post("/api/v1/auth/register", json={"email": "spec6@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "spec6@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=VALID_OPENAPI3_YAML):
        disc_res = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.example.com/openapi.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )
    spec_id = disc_res.json()["id"]

    # Test GET /specifications list
    list_res = client.get("/api/v1/openapi/specifications", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Test GET /specifications/{spec_id} detail
    detail_res = client.get(f"/api/v1/openapi/specifications/{spec_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == spec_id
    assert len(detail_res.json()["operations"]) == 2
