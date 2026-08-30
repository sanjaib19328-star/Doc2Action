from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# In-memory SQLite database setup for E2E integration test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

REAL_INTEGRATED_SPEC_YAML = """
openapi: 3.0.0
info:
  title: Integrated Stripe Payments API
  version: 2024-01-01
servers:
  - url: https://api.stripe.com/v1
paths:
  /customers/{customerId}:
    get:
      operationId: getCustomer
      summary: Retrieve a customer
      parameters:
        - name: customerId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Customer details
  /refunds:
    post:
      operationId: createRefund
      summary: Create a refund
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                charge:
                  type: string
                amount:
                  type: integer
      responses:
        '200':
          description: Refund object
"""


def run_e2e_integration_flow():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        print("=== STEP 1: Health Checks ===")
        h_res = client.get("/api/v1/health")
        assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
        print("Health Status:", h_res.json())

        print("\n=== STEP 2: User Registration & Login ===")
        email = "e2e_auditor@example.com"
        passw = "SecurePass123!"
        reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": passw, "full_name": "E2E Auditor"})
        assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"

        login_res = client.post("/api/v1/auth/login", json={"email": email, "password": passw})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in successfully. Token acquired.")

        print("\n=== STEP 3: Discover OpenAPI Specification ===")
        with patch("app.modules.openapi.service.fetch_spec_from_url", return_value=REAL_INTEGRATED_SPEC_YAML):
            disc_res = client.post("/api/v1/openapi/discover", json={"url": "https://api.stripe.com/spec.yaml"}, headers=headers)
        assert disc_res.status_code == 201, f"Discover failed: {disc_res.text}"
        spec_data = disc_res.json()
        spec_id = spec_data["id"]
        print(f"Discovered Spec '{spec_data['title']}' with {len(spec_data['operations'])} operations.")

        print("\n=== STEP 4: Create API Catalog Connection ===")
        conn_res = client.post(
            "/api/v1/catalog/connections",
            json={
                "specification_id": spec_id,
                "name": "Stripe Production",
                "auth_config": {"type": "bearer", "token": "sk_test_mock123456789"},
            },
            headers=headers,
        )
        assert conn_res.status_code == 201, f"Connection failed: {conn_res.text}"
        conn_data = conn_res.json()
        conn_id = conn_data["id"]
        endpoints = conn_data["endpoints"]
        refund_endpoint = next(ep for ep in endpoints if ep["operation_id"] == "createRefund")
        refund_endpoint_id = refund_endpoint["id"]
        print(f"Connection created (ID: {conn_id}) with {len(endpoints)} catalog endpoints.")

        print("\n=== STEP 5: Index Knowledge Base & Semantic Search ===")
        idx_res = client.post(f"/api/v1/rag/index/{conn_id}", headers=headers)
        assert idx_res.status_code == 200, f"Index failed: {idx_res.text}"
        print(f"Indexed {idx_res.json()['indexed_count']} endpoints into RAG knowledge base.")

        search_res = client.post("/api/v1/rag/search", json={"query": "process refund charge"}, headers=headers)
        assert search_res.status_code == 200, f"Search failed: {search_res.text}"
        search_hits = search_res.json()
        assert len(search_hits) > 0
        print(f"Semantic search returned top result: {search_hits[0]['operation_id']} - {search_hits[0]['path']}")

        print("\n=== STEP 6: Propose Action (Human-in-the-Loop) ===")
        prop_res = client.post(
            "/api/v1/verification/propose",
            json={
                "endpoint_id": refund_endpoint_id,
                "intent_summary": "Process refund for charge ch_3Mv123 for $50",
                "body": {"charge": "ch_3Mv123", "amount": 5000},
            },
            headers=headers,
        )
        assert prop_res.status_code == 201, f"Proposal failed: {prop_res.text}"
        prop_data = prop_res.json()
        proposal_id = prop_data["proposal_id"]
        print(f"Action Proposal Created (ID: {proposal_id}) -> Status: {prop_data['status']}")
        print(f"Target URL: {prop_data['target_url']}")
        print(f"Masked Headers: {prop_data['headers']}")

        print("\n=== STEP 7: Confirm Action Proposal ===")
        conf_res = client.post(f"/api/v1/verification/proposals/{proposal_id}/confirm", headers=headers)
        assert conf_res.status_code == 200, f"Confirm failed: {conf_res.text}"
        assert conf_res.json()["status"] == "confirmed"
        print("Action proposal status confirmed.")

        print("\n=== STEP 8: Execute Confirmed Action & Audit Log ===")
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "re_1001", "status": "succeeded", "amount": 5000}
            mock_response.text = '{"id": "re_1001", "status": "succeeded", "amount": 5000}'
            mock_client.request.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_client

            exec_res = client.post(f"/api/v1/verification/proposals/{proposal_id}/execute", headers=headers)

        assert exec_res.status_code == 200, f"Execute failed: {exec_res.text}"
        exec_data = exec_res.json()
        assert exec_data["status"] == "executed"
        result = exec_data["execution_result"]
        assert result["status"] == "success"
        print("Execution Succeeded!")
        print("Result Payload:", result["response_body"])
        print("Latency:", result["latency_ms"], "ms")

        print("\n=== STEP 9: Audit Logs Verification ===")
        logs_res = client.get("/api/v1/execution/logs", headers=headers)
        assert logs_res.status_code == 200
        logs = logs_res.json()
        assert len(logs) == 1
        assert logs[0]["target_url"] == "https://api.stripe.com/v1/refunds"
        print("Execution audit log confirmed in database.")

        print("\n=======================================================")
        print("=== INTEGRATED BACKEND END-TO-END FLOW: PASSED 100% ===")
        print("=======================================================")

    finally:
        app.dependency_overrides.clear()
        db_session.close()
        Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    run_e2e_integration_flow()
