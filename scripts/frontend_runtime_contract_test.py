import sys
import json
import httpx

BASE_URL = "http://127.0.0.1:8000"

print("="*80)
print("  FRONTEND INTERACTION & NETWORK CONTRACT VERIFICATION TEST SUITE  ")
print("="*80)

client = httpx.Client(timeout=15.0)

test_results = []

def record(name, url, method, request, status, details, result=True):
    test_results.append({
        "name": name,
        "url": url,
        "method": method,
        "request": request,
        "status": status,
        "details": details,
        "result": "PASS" if result else "FAIL"
    })
    status_str = "PASS" if result else "FAIL"
    print(f"[{status_str}] {name:<35} | {method:<4} {url:<45} -> Status: {status}")

# 1. Health Checks
res = client.get(f"{BASE_URL}/health")
record("Health Check", "/health", "GET", None, res.status_code, "Root health OK", res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/health")
record("API v1 Health Check", "/api/v1/health", "GET", None, res.status_code, "API health OK", res.status_code == 200)

# 2. Login Page & JWT token acquisition
login_payload = {"email": "gate_user@doc2action.io", "password": "GatePassword123!"}
res = client.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
token = res.json().get("access_token") if res.status_code == 200 else None
record("Login (POST /auth/login)", "/api/v1/auth/login", "POST", login_payload["email"], res.status_code, f"Bearer token issued: {token[:15]}...", res.status_code == 200 and token is not None)

headers = {"Authorization": f"Bearer {token}"} if token else {}

# 3. Authenticated Get Me
res = client.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
record("Get Current User (/auth/me)", "/api/v1/auth/me", "GET", "Authorization: Bearer <token>", res.status_code, f"User: {res.json().get('email')}", res.status_code == 200 and res.json().get('email') == login_payload["email"])

# 4. Dashboard calls
res = client.get(f"{BASE_URL}/api/v1/openapi/specifications", headers=headers)
specs_count = len(res.json()) if res.status_code == 200 else 0
record("Dashboard: List Specs", "/api/v1/openapi/specifications", "GET", None, res.status_code, f"Count: {specs_count}", res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/catalog/connections", headers=headers)
conns = res.json() if res.status_code == 200 else []
record("Dashboard: List Connections", "/api/v1/catalog/connections", "GET", None, res.status_code, f"Count: {len(conns)}", res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/verification/proposals", headers=headers)
props = res.json() if res.status_code == 200 else []
record("Dashboard: List Proposals", "/api/v1/verification/proposals", "GET", None, res.status_code, f"Count: {len(props)}", res.status_code == 200)

res = client.get(f"{BASE_URL}/api/v1/execution/logs", headers=headers)
logs = res.json() if res.status_code == 200 else []
record("Dashboard: List Execution Logs", "/api/v1/execution/logs", "GET", None, res.status_code, f"Count: {len(logs)}", res.status_code == 200)

# 5. OpenAPI Discovery Page
discover_payload = {"url": "https://petstore.swagger.io/v2/swagger.json"}
res = client.post(f"{BASE_URL}/api/v1/openapi/discover", json=discover_payload, headers=headers)
spec_id = res.json().get("id") if res.status_code == 201 else None
record("OpenAPI Discovery (POST /discover)", "/api/v1/openapi/discover", "POST", discover_payload["url"], res.status_code, f"Spec ID: {spec_id}", res.status_code == 201)

if spec_id:
    res = client.get(f"{BASE_URL}/api/v1/openapi/specifications/{spec_id}", headers=headers)
    record("Get Specification Details", f"/api/v1/openapi/specifications/{spec_id[:8]}...", "GET", None, res.status_code, f"Operations: {len(res.json().get('operations', []))}", res.status_code == 200)

# 6. Catalog Page & Connection Detail Page
conn_id = None
find_status_ep_id = None
if spec_id:
    conn_create_payload = {
        "specification_id": spec_id,
        "name": "Frontend Verification Petstore",
        "auth_config": {"type": "none"}
    }
    res = client.post(f"{BASE_URL}/api/v1/catalog/connections", json=conn_create_payload, headers=headers)
    if res.status_code == 201:
        conn_id = res.json().get("id")
        endpoints = res.json().get("endpoints", [])
        for ep in endpoints:
            if ep.get("path") == "/pet/findByStatus":
                find_status_ep_id = ep.get("id")
        if not find_status_ep_id and endpoints:
            find_status_ep_id = endpoints[0].get("id")
    record("Create Connection", "/api/v1/catalog/connections", "POST", conn_create_payload["name"], res.status_code, f"Conn ID: {conn_id}", res.status_code == 201)

if conn_id:
    res = client.get(f"{BASE_URL}/api/v1/catalog/connections/{conn_id}", headers=headers)
    record("Get Connection Detail", f"/api/v1/catalog/connections/{conn_id[:8]}...", "GET", None, res.status_code, f"Name: {res.json().get('name')}", res.status_code == 200)

    res = client.get(f"{BASE_URL}/api/v1/catalog/connections/{conn_id}/endpoints", headers=headers)
    record("Get Connection Endpoints", f"/api/v1/catalog/connections/{conn_id[:8]}.../endpoints", "GET", None, res.status_code, f"Endpoints: {len(res.json())}", res.status_code == 200)

# 7. RAG Indexing & Search Page
if conn_id:
    res = client.post(f"{BASE_URL}/api/v1/rag/index/{conn_id}", headers=headers)
    record("RAG Index Connection", f"/api/v1/rag/index/{conn_id[:8]}...", "POST", None, res.status_code, f"Indexed: {res.json().get('indexed_count')}", res.status_code == 200)

rag_search_payload = {"query": "find pet by status"}
res = client.post(f"{BASE_URL}/api/v1/rag/search", json=rag_search_payload, headers=headers)
hits = res.json() if res.status_code == 200 else []
record("RAG Search", "/api/v1/rag/search", "POST", rag_search_payload["query"], res.status_code, f"Hits: {len(hits)}", res.status_code == 200)

# 8. Human Verification Page Flow
proposal_id = None
if find_status_ep_id:
    propose_payload = {
        "endpoint_id": find_status_ep_id,
        "intent_summary": "Frontend verification find pets",
        "query_params": {"status": "available"}
    }
    res = client.post(f"{BASE_URL}/api/v1/verification/propose", json=propose_payload, headers=headers)
    proposal_id = res.json().get("proposal_id") if res.status_code == 201 else None
    record("Verification Propose", "/api/v1/verification/propose", "POST", propose_payload["intent_summary"], res.status_code, f"Proposal ID: {proposal_id}", res.status_code == 201)

if proposal_id:
    res = client.post(f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/confirm", headers=headers)
    record("Verification Confirm", f"/api/v1/verification/proposals/{proposal_id[:8]}.../confirm", "POST", None, res.status_code, f"Status: {res.json().get('status')}", res.status_code == 200 and res.json().get("status") == "confirmed")

    res = client.post(f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/execute", headers=headers)
    record("Verification Execute", f"/api/v1/verification/proposals/{proposal_id[:8]}.../execute", "POST", None, res.status_code, f"Status: {res.json().get('status')}", res.status_code == 200 and res.json().get("status") == "executed")

# 9. Execution Logs Page
res = client.get(f"{BASE_URL}/api/v1/execution/logs", headers=headers)
record("Execution Audit Logs", "/api/v1/execution/logs", "GET", None, res.status_code, f"Logs retrieved: {len(res.json())}", res.status_code == 200)

# 10. Clean up test connection
if conn_id:
    client.delete(f"{BASE_URL}/api/v1/catalog/connections/{conn_id}", headers=headers)

print("="*80)
failures = [r for r in test_results if r["result"] == "FAIL"]
if failures:
    print(f"FAILED TESTS: {len(failures)}")
    sys.exit(1)
else:
    print("ALL RUNTIME NETWORK TESTS PASSED 100%!")
    sys.exit(0)
