import sys
import json
import httpx
import psycopg2

BASE_URL = "http://127.0.0.1:8000"
DB_CONN = "postgresql://doc2action:doc2action_dev_password@127.0.0.1:5432/doc2action"

client = httpx.Client(timeout=10.0)

# Matrix records
matrix_rows = []

def record_test(endpoint, method, auth, expected, actual, result, details=""):
    matrix_rows.append({
        "endpoint": endpoint,
        "method": method,
        "auth": "Yes" if auth else "No",
        "expected": expected,
        "actual": actual,
        "result": "PASS" if result else "FAIL",
        "details": details
    })

print("Running Full Backend Completion Gate Tests against Live Server...")

# 1. Health Endpoints
res = client.get(f"{BASE_URL}/health")
record_test("/health", "GET", False, 200, res.status_code, res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/health")
record_test("/api/v1/health", "GET", False, 200, res.status_code, res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/health/db")
record_test("/api/v1/health/db", "GET", False, 200, res.status_code, res.status_code == 200)

# 2. OpenAPI JSON Schema Validation
res = client.get(f"{BASE_URL}/api/v1/openapi.json")
record_test("/api/v1/openapi.json", "GET", False, 200, res.status_code, res.status_code == 200 and "openapi" in res.json())
openapi_spec = res.json() if res.status_code == 200 else {}

# 3. Auth Endpoints
# Unauthenticated /auth/me should return 401
res = client.get(f"{BASE_URL}/api/v1/auth/me")
record_test("/api/v1/auth/me (Unauthenticated)", "GET", True, 401, res.status_code, res.status_code == 401)

# Register user
email = "gate_user@doc2action.io"
password = "GatePassword123!"
res = client.post(f"{BASE_URL}/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Gate Tester"})
record_test("/api/v1/auth/register", "POST", False, "201 or 400", res.status_code, res.status_code in [201, 400])

# JSON Login
res = client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
token = res.json().get("access_token") if res.status_code == 200 else None
record_test("/api/v1/auth/login (JSON)", "POST", False, 200, res.status_code, res.status_code == 200 and token is not None)

headers = {"Authorization": f"Bearer {token}"} if token else {}

# Form Login
res = client.post(f"{BASE_URL}/api/v1/auth/token", data={"username": email, "password": password})
record_test("/api/v1/auth/token (OAuth2 Form)", "POST", False, 200, res.status_code, res.status_code == 200 and "access_token" in res.json())

# Authenticated /auth/me
res = client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
record_test("/api/v1/auth/me (Authenticated)", "GET", True, 200, res.status_code, res.status_code == 200 and res.json().get("email") == email)

# 4. OpenAPI Discovery & Specifications
# SSRF Protection test (Internal IP attempt)
res = client.post(f"{BASE_URL}/api/v1/openapi/discover", json={"url": "http://169.254.169.254/latest/meta-data/"}, headers=headers)
record_test("/api/v1/openapi/discover (SSRF Block)", "POST", True, 400, res.status_code, res.status_code == 400, "SSRF attempt blocked")

# Valid Discovery
res = client.post(f"{BASE_URL}/api/v1/openapi/discover", json={"url": "https://petstore.swagger.io/v2/swagger.json"}, headers=headers)
record_test("/api/v1/openapi/discover", "POST", True, 201, res.status_code, res.status_code == 201)
spec_id = res.json().get("id") if res.status_code == 201 else None

# List Specifications
res = client.get(f"{BASE_URL}/api/v1/openapi/specifications", headers=headers)
record_test("/api/v1/openapi/specifications", "GET", True, 200, res.status_code, res.status_code == 200 and isinstance(res.json(), list))

# Get Specification by ID
if spec_id:
    res = client.get(f"{BASE_URL}/api/v1/openapi/specifications/{spec_id}", headers=headers)
    record_test(f"/api/v1/openapi/specifications/{spec_id}", "GET", True, 200, res.status_code, res.status_code == 200)

# Invalid Spec ID (404 test)
fake_uuid = "00000000-0000-0000-0000-000000000000"
res = client.get(f"{BASE_URL}/api/v1/openapi/specifications/{fake_uuid}", headers=headers)
record_test("/api/v1/openapi/specifications/{fake_id} (404 Test)", "GET", True, 404, res.status_code, res.status_code == 404)

# 5. Catalog Connections
conn_id = None
endpoint_id = None
if spec_id:
    res = client.post(f"{BASE_URL}/api/v1/catalog/connections", json={
        "specification_id": spec_id,
        "name": "Gate Petstore Connection",
        "auth_config": {"type": "none"}
    }, headers=headers)
    record_test("/api/v1/catalog/connections", "POST", True, 201, res.status_code, res.status_code == 201)
    if res.status_code == 201:
        conn_id = res.json().get("id")
        endpoints = res.json().get("endpoints", [])
        for ep in endpoints:
            if ep.get("path") == "/pet/findByStatus":
                endpoint_id = ep.get("id")
        if not endpoint_id and endpoints:
            endpoint_id = endpoints[0].get("id")

res = client.get(f"{BASE_URL}/api/v1/catalog/connections", headers=headers)
record_test("/api/v1/catalog/connections", "GET", True, 200, res.status_code, res.status_code == 200 and isinstance(res.json(), list))

if conn_id:
    res = client.get(f"{BASE_URL}/api/v1/catalog/connections/{conn_id}", headers=headers)
    record_test("/api/v1/catalog/connections/{id}", "GET", True, 200, res.status_code, res.status_code == 200)

    res = client.get(f"{BASE_URL}/api/v1/catalog/connections/{conn_id}/endpoints", headers=headers)
    record_test("/api/v1/catalog/connections/{id}/endpoints", "GET", True, 200, res.status_code, res.status_code == 200)

# 6. RAG Endpoints
if conn_id:
    res = client.post(f"{BASE_URL}/api/v1/rag/index/{conn_id}", headers=headers)
    record_test("/api/v1/rag/index/{connection_id}", "POST", True, 200, res.status_code, res.status_code == 200)

    res = client.post(f"{BASE_URL}/api/v1/rag/reindex/{conn_id}", headers=headers)
    record_test("/api/v1/rag/reindex/{connection_id}", "POST", True, 200, res.status_code, res.status_code == 200)

res = client.post(f"{BASE_URL}/api/v1/rag/search", json={"query": "find pet"}, headers=headers)
record_test("/api/v1/rag/search", "POST", True, 200, res.status_code, res.status_code == 200)

# 7. Verification / Human-in-the-Loop
proposal_id = None
if endpoint_id:
    res = client.post(f"{BASE_URL}/api/v1/verification/propose", json={
        "endpoint_id": endpoint_id,
        "intent_summary": "Gate test find pets by status",
        "query_params": {"status": "available"}
    }, headers=headers)
    record_test("/api/v1/verification/propose", "POST", True, 201, res.status_code, res.status_code == 201)
    if res.status_code == 201:
        proposal_id = res.json().get("proposal_id")

res = client.get(f"{BASE_URL}/api/v1/verification/proposals", headers=headers)
record_test("/api/v1/verification/proposals", "GET", True, 200, res.status_code, res.status_code == 200 and isinstance(res.json(), list))

if proposal_id:
    res = client.get(f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}", headers=headers)
    record_test("/api/v1/verification/proposals/{id}", "GET", True, 200, res.status_code, res.status_code == 200)

    # Execution before confirmation should fail (400 validation)
    res = client.post(f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/execute", headers=headers)
    record_test("/api/v1/verification/proposals/{id}/execute (Unconfirmed 400)", "POST", True, 400, res.status_code, res.status_code == 400, "Blocked execution of unconfirmed proposal")

    # Confirm proposal
    res = client.post(f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/confirm", headers=headers)
    record_test("/api/v1/verification/proposals/{id}/confirm", "POST", True, 200, res.status_code, res.status_code == 200 and res.json().get("status") == "confirmed")

    # Execute proposal
    res = client.post(f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/execute", headers=headers)
    record_test("/api/v1/verification/proposals/{id}/execute", "POST", True, 200, res.status_code, res.status_code == 200 and res.json().get("status") == "executed")

# 8. Execution Engine
if endpoint_id:
    res = client.post(f"{BASE_URL}/api/v1/execution/preview", json={
        "endpoint_id": endpoint_id,
        "query_params": {"status": "available"}
    }, headers=headers)
    record_test("/api/v1/execution/preview", "POST", True, 200, res.status_code, res.status_code == 200)

    res = client.post(f"{BASE_URL}/api/v1/execution/execute", json={
        "endpoint_id": endpoint_id,
        "query_params": {"status": "available"},
        "confirmed": True
    }, headers=headers)
    record_test("/api/v1/execution/execute", "POST", True, 200, res.status_code, res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/execution/logs", headers=headers)
record_test("/api/v1/execution/logs", "GET", True, 200, res.status_code, res.status_code == 200 and isinstance(res.json(), list))
log_id = res.json()[0].get("id") if res.status_code == 200 and res.json() else None

if log_id:
    res = client.get(f"{BASE_URL}/api/v1/execution/logs/{log_id}", headers=headers)
    record_test(f"/api/v1/execution/logs/{log_id}", "GET", True, 200, res.status_code, res.status_code == 200)

# Delete Connection & RAG Index
if conn_id:
    res = client.delete(f"{BASE_URL}/api/v1/rag/index/{conn_id}", headers=headers)
    record_test("/api/v1/rag/index/{connection_id}", "DELETE", True, 200, res.status_code, res.status_code == 200)

    res = client.delete(f"{BASE_URL}/api/v1/catalog/connections/{conn_id}", headers=headers)
    record_test("/api/v1/catalog/connections/{connection_id}", "DELETE", True, 200, res.status_code, res.status_code == 200)

# Print Matrix
print("\n" + "="*95)
print("                       LIVE API VERIFICATION MATRIX                       ")
print("="*95)
print(f"| {'Endpoint':<55} | {'Method':<6} | {'Auth':<4} | {'Expected':<10} | {'Actual':<6} | {'Result':<6} |")
print("|" + "-"*57 + "|" + "-"*8 + "|" + "-"*6 + "|" + "-"*12 + "|" + "-"*8 + "|" + "-"*8 + "|")
for r in matrix_rows:
    print(f"| {r['endpoint']:<55} | {r['method']:<6} | {r['auth']:<4} | {str(r['expected']):<10} | {str(r['actual']):<6} | {r['result']:<6} |")
print("="*95)

# Check for any failures
failures = [r for r in matrix_rows if r["result"] == "FAIL"]
if failures:
    print(f"\nCRITICAL: {len(failures)} tests failed!")
    sys.exit(1)
else:
    print("\nALL BACKEND COMPLETION GATE TESTS PASSED 100%!")
    sys.exit(0)
