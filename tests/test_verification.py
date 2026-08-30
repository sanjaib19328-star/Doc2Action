import uuid
import pytest
from unittest.mock import patch, MagicMock

VERIF_SPEC_YAML = """
openapi: 3.0.0
info:
  title: Orders Management Service
  version: 1.0.0
servers:
  - url: https://api.orderservice.com/v1
paths:
  /orders/{orderId}/cancel:
    post:
      operationId: cancelOrder
      summary: Cancel an existing order
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
      responses:
        '200':
          description: Order cancelled successfully
"""


def _setup_user_and_token(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login_res.json()["access_token"]


def _setup_catalog_and_endpoint(client, token):
    with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=VERIF_SPEC_YAML):
        spec_res = client.post(
            "/api/v1/openapi/discover",
            json={"url": "https://api.orderservice.com/spec.yaml"},
            headers={"Authorization": f"Bearer {token}"},
        )
    spec_id = spec_res.json()["id"]

    conn_res = client.post(
        "/api/v1/catalog/connections",
        json={
            "specification_id": spec_id,
            "name": "Orders Service",
            "auth_config": {"type": "bearer", "token": "secret-auth-token-xyz"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    conn_data = conn_res.json()
    endpoint_id = conn_data["endpoints"][0]["id"]
    return conn_data["id"], endpoint_id


def test_proposal_creation_and_validation(client):
    """Test proposing an action validates endpoint parameters and constructs proposal preview."""
    token = _setup_user_and_token(client, "verif1@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id,
            "intent_summary": "Cancel order #ORD-12345 due to customer request",
            "path_params": {"orderId": "ORD-12345"},
            "body": {"reason": "Customer request"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prop_res.status_code == 201
    data = prop_res.json()
    assert data["intent_summary"] == "Cancel order #ORD-12345 due to customer request"
    assert data["target_url"] == "https://api.orderservice.com/v1/orders/ORD-12345/cancel"
    assert data["http_method"] == "POST"
    assert data["status"] == "pending"
    assert "proposal_id" in data


def test_proposal_creation_missing_param_fails(client):
    """Test proposing an action fails if required path parameter is missing."""
    token = _setup_user_and_token(client, "verif2@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id,
            "intent_summary": "Cancel order",
            "path_params": {},  # missing orderId
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prop_res.status_code == 400
    assert "Missing required path parameter" in prop_res.json()["error"]["message"]


def test_execute_unconfirmed_proposal_fails(client):
    """Test executing a pending (unconfirmed) proposal is strictly rejected."""
    token = _setup_user_and_token(client, "verif3@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id,
            "intent_summary": "Cancel order #ORD-888",
            "path_params": {"orderId": "ORD-888"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    proposal_id = prop_res.json()["proposal_id"]

    # Attempt to execute without confirmation
    exec_res = client.post(
        f"/api/v1/verification/proposals/{proposal_id}/execute",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exec_res.status_code == 400
    assert "Unconfirmed action proposal cannot be executed" in exec_res.json()["error"]["message"]


def test_proposal_confirmation_and_execution_lifecycle(client):
    """Test full human-in-the-loop lifecycle: Propose -> Confirm -> Execute -> Audit Result."""
    token = _setup_user_and_token(client, "verif4@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    # 1. Propose
    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id,
            "intent_summary": "Cancel order #ORD-999",
            "path_params": {"orderId": "ORD-999"},
            "body": {"reason": "Out of stock"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    proposal_id = prop_res.json()["proposal_id"]

    # 2. Confirm
    conf_res = client.post(
        f"/api/v1/verification/proposals/{proposal_id}/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "confirmed"

    # 3. Execute
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cancelled": True, "orderId": "ORD-999"}
        mock_response.text = '{"cancelled": true, "orderId": "ORD-999"}'
        mock_client.request.return_value = mock_response
        mock_client_cls.return_value.__enter__.return_value = mock_client

        exec_res = client.post(
            f"/api/v1/verification/proposals/{proposal_id}/execute",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert exec_res.status_code == 200
    data = exec_res.json()
    assert data["status"] == "executed"
    assert data["execution_result"]["status"] == "success"
    assert data["execution_result"]["response_body"] == {"cancelled": True, "orderId": "ORD-999"}


def test_proposal_rejection(client):
    """Test rejecting a proposal prevents subsequent execution."""
    token = _setup_user_and_token(client, "verif5@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id,
            "intent_summary": "Cancel order #ORD-101",
            "path_params": {"orderId": "ORD-101"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    proposal_id = prop_res.json()["proposal_id"]

    # Reject proposal
    rej_res = client.post(
        f"/api/v1/verification/proposals/{proposal_id}/reject",
        json={"reason": "User changed mind"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # Attempt to execute rejected proposal -> fails
    exec_res = client.post(
        f"/api/v1/verification/proposals/{proposal_id}/execute",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exec_res.status_code == 400
    assert "Cannot execute a rejected action proposal" in exec_res.json()["error"]["message"]


def test_expired_proposal_handling(client, db):
    """Test that expired proposals cannot be confirmed or executed."""
    token = _setup_user_and_token(client, "verif6@example.com")
    conn_id, endpoint_id = _setup_catalog_and_endpoint(client, token)

    # Propose with short TTL (30s)
    prop_res = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id,
            "intent_summary": "Cancel order #ORD-000",
            "path_params": {"orderId": "ORD-000"},
            "ttl_seconds": 30,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    proposal_id = prop_res.json()["proposal_id"]

    # Manually expire in DB for fast testing
    from app.modules.verification.models import APIActionProposal
    from datetime import datetime, timedelta, timezone

    p = db.query(APIActionProposal).filter(APIActionProposal.id == uuid.UUID(proposal_id)).first()
    p.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db.commit()

    # Confirm attempt on expired proposal -> fails
    conf_res = client.post(
        f"/api/v1/verification/proposals/{proposal_id}/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert conf_res.status_code == 400
    assert "expired" in conf_res.json()["error"]["message"].lower()


def test_user_proposal_isolation(client):
    """Test strict user isolation for action proposals."""
    token_a = _setup_user_and_token(client, "propusera@example.com")
    token_b = _setup_user_and_token(client, "propuserb@example.com")

    conn_id_a, endpoint_id_a = _setup_catalog_and_endpoint(client, token_a)

    prop_res_a = client.post(
        "/api/v1/verification/propose",
        json={
            "endpoint_id": endpoint_id_a,
            "intent_summary": "User A action",
            "path_params": {"orderId": "ORD-AAA"},
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    proposal_id_a = prop_res_a.json()["proposal_id"]

    # User B attempts to access User A's proposal -> 404
    get_b = client.get(
        f"/api/v1/verification/proposals/{proposal_id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_b.status_code == 404

    # User B attempts to confirm User A's proposal -> 404
    conf_b = client.post(
        f"/api/v1/verification/proposals/{proposal_id_a}/confirm",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert conf_b.status_code == 404
