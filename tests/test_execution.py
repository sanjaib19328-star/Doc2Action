import uuid
import pytest
from unittest.mock import patch, MagicMock
from app.modules.execution.builder import mask_sensitive_headers

EXEC_SPEC_YAML = """
openapi: 3.0.0
info:
  title: Users Service API
  version: 1.0.0
servers:
  - url: https://api.userservice.com/v1
paths:
  /users/{userId}:
    get:
      operationId: getUserById
      summary: Get user details
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
        - name: verbose
          in: query
          required: false
          schema:
            type: boolean
      responses:
        '200':
          description: User profile details
"""


def _setup_user_and_token(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login_res.json()["access_token"]


def _setup_catalog_and_endpoint(client, token):
    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=EXEC_SPEC_YAML):
        spec_res = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.userservice.com/spec.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )
    spec_id = spec_res.json()["id"]

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={
            "specification_id": spec_id,
            "name": "User Service",
            "auth_config": {"type": "bearer", "token": "secret-bearer-token-12345"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    conn_data = conn_res.json()
    endpoint_id = conn_data["endpoints"][0]["id"]
    return conn_data["id"], endpoint_id


def test_mask_sensitive_headers():
    """Test masking sensitive header values."""
    headers = {
        "Authorization": "Bearer supersecretjwttoken",
        "X-API-Key": "my-secret-key-12345",
        "Content-Type": "application/json",
    }
    masked = mask_sensitive_headers(headers)
    assert "supersecretjwttoken" not in masked["Authorization"]
    assert "my-secret-key-12345" not in masked["X-API-Key"]
    assert masked["Content-Type"] == "application/json"


def test_execution_preview(client):
    """Test previewing an execution request validates path parameters and masks headers without making HTTP calls."""
    token = _setup_user_and_token(client, "prev1@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    preview_res = client.post(
        "/api/v1/execution/preview",
        json={
            "endpoint_id": endpoint_id,
            "path_params": {"userId": "usr_999"},
            "query_params": {"verbose": True},
            "headers": {"X-Custom": "HeaderVal"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert preview_res.status_code == 200
    data = preview_res.json()
    assert data["target_url"] == "https://api.userservice.com/v1/users/usr_999"
    assert data["method"] == "GET"
    assert "Authorization" in data["masked_headers"]
    assert "supersecret" not in data["masked_headers"]["Authorization"]


def test_execution_preview_missing_path_param_fails(client):
    """Test preview fails if required path parameter is missing."""
    token = _setup_user_and_token(client, "prev2@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    preview_res = client.post(
        "/api/v1/execution/preview",
        json={
            "endpoint_id": endpoint_id,
            "path_params": {},  # missing userId
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert preview_res.status_code == 400
    assert "Missing required path parameter" in preview_res.json()["error"]["message"]


def test_execute_without_confirmation_fails(client):
    """Test executing request without confirmed=True is rejected."""
    token = _setup_user_and_token(client, "exec1@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    exec_res = client.post(
        "/api/v1/execution/execute",
        json={
            "endpoint_id": endpoint_id,
            "path_params": {"userId": "usr_100"},
            "confirmed": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exec_res.status_code == 400
    assert "Human confirmation required" in exec_res.json()["error"]["message"]


def test_execute_unregistered_endpoint_fails(client):
    """Test attempting to execute an arbitrary endpoint ID not in user catalog fails."""
    token = _setup_user_and_token(client, "exec2@example.com")
    fake_endpoint_id = str(uuid.uuid4())

    exec_res = client.post(
        "/api/v1/execution/execute",
        json={
            "endpoint_id": fake_endpoint_id,
            "path_params": {},
            "confirmed": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exec_res.status_code == 404
    assert "Endpoint not found in user's registered API catalog" in exec_res.json()["error"]["message"]


def test_execute_api_call_and_record_log(client):
    """Test successful API execution with mocked HTTP response and log verification."""
    token = _setup_user_and_token(client, "exec3@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    mock_httpx_response = MagicMock()
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"id": "usr_555", "name": "Alice"}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "usr_555", "name": "Alice"}
        mock_response.text = '{"id": "usr_555", "name": "Alice"}'
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        exec_res = client.post(
            "/api/v1/execution/execute",
            json={
                "endpoint_id": endpoint_id,
                "path_params": {"userId": "usr_555"},
                "confirmed": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    if exec_res.status_code != 200:
        pytest.fail(f"Execution failed: {exec_res.status_code} - {exec_res.text}")

    assert exec_res.status_code == 200
    data = exec_res.json()
    assert data["status"] == "success"
    assert data["status_code"] == 200
    assert data["target_url"] == "https://api.userservice.com/v1/users/usr_555"
    assert data["response_body"] == {"id": "usr_555", "name": "Alice"}
    assert "execution_id" in data
    assert data["latency_ms"] >= 0.0

    # Retrieve execution logs endpoint
    logs_res = client.get("/api/v1/execution/logs", headers={"Authorization": f"Bearer {token}"})
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) == 1
    assert logs[0]["target_url"] == "https://api.userservice.com/v1/users/usr_555"


def test_user_execution_isolation(client):
    """Test strict user isolation for execution and execution logs."""
    token_a = _setup_user_and_token(client, "execloga@example.com")
    token_b = _setup_user_and_token(client, "execlogb@example.com")

    conn_id_a, endpoint_id_a = _setup_catalog_and_endpoint(client, token_a)

    # User B tries to execute User A's catalog endpoint -> 404
    exec_res_b = client.post(
        "/api/v1/execution/execute",
        json={
            "endpoint_id": endpoint_id_a,
            "path_params": {"userId": "usr_111"},
            "confirmed": True,
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert exec_res_b.status_code == 404

    # User B logs must remain empty
    logs_b = client.get("/api/v1/execution/logs", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(logs_b) == 0
