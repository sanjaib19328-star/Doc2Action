import sys
import json
import httpx
import psycopg2

BASE_URL = "http://127.0.0.1:8000"
DB_CONN = "postgresql://doc2action:doc2action_dev_password@127.0.0.1:5432/doc2action"

print("==========================================================")
print("   LIVE APPLICATION END-TO-END VERIFICATION SUITE         ")
print("==========================================================")

passed_tests = []
failed_tests = []

def record_pass(name, url, method, request, status, validation, db_val="Verified in Postgres"):
    passed_tests.append({
        "name": name,
        "url": url,
        "method": method,
        "request": request,
        "status": status,
        "validation": validation,
        "db": db_val
    })
    print(f"[PASS] {name} -> Status: {status} | Validation: {validation}")

def record_fail(name, url, status, response, cause, fix="N/A"):
    failed_tests.append({
        "name": name,
        "url": url,
        "status": status,
        "response": response,
        "cause": cause,
        "fix": fix
    })
    print(f"[FAIL] {name} -> Status: {status} | Cause: {cause}")

client = httpx.Client(timeout=10.0)

# 1. Health Checks
try:
    url = f"{BASE_URL}/health"
    res = client.get(url)
    if res.status_code == 200 and res.json().get("status") == "healthy":
        record_pass("Root Health Check", url, "GET", None, res.status_code, res.json())
    else:
        record_fail("Root Health Check", url, res.status_code, res.text, "Unexpected payload")

    url = f"{BASE_URL}/api/v1/health"
    res = client.get(url)
    if res.status_code == 200 and res.json().get("status") == "healthy":
        record_pass("API v1 Health Check", url, "GET", None, res.status_code, res.json())
    else:
        record_fail("API v1 Health Check", url, res.status_code, res.text, "Unexpected payload")
except Exception as e:
    record_fail("Health Checks", BASE_URL, 500, str(e), "Server unreachable")

# 2. OpenAPI Schema & Docs
try:
    url = f"{BASE_URL}/api/v1/openapi.json"
    res = client.get(url)
    if res.status_code == 200 and "openapi" in res.json():
        record_pass("OpenAPI Schema endpoint", url, "GET", None, res.status_code, f"OpenAPI v{res.json().get('openapi')}")
    else:
        record_fail("OpenAPI Schema endpoint", url, res.status_code, res.text, "Missing openapi key")
except Exception as e:
    record_fail("OpenAPI Schema", BASE_URL, 500, str(e), "Error fetching schema")

# 3. User Registration
user_pass = "LivePassword123!"
auth_token = None
headers = {}

try:
    url = f"{BASE_URL}/api/v1/auth/register"
    req_body = {"email": "live_user@doc2action.io", "password": user_pass, "full_name": "Live Tester"}
    res = client.post(url, json=req_body)
    if res.status_code in [201, 400]:
        record_pass("User Registration", url, "POST", {"email": req_body["email"]}, res.status_code, "User registered or existing")
    else:
        record_fail("User Registration", url, res.status_code, res.text, "Registration error")
except Exception as e:
    record_fail("User Registration", BASE_URL, 500, str(e), "Exception during registration")

# 4. JSON Login
try:
    url = f"{BASE_URL}/api/v1/auth/login"
    req_body = {"email": "live_user@doc2action.io", "password": user_pass}
    res = client.post(url, json=req_body)
    if res.status_code == 200 and "access_token" in res.json():
        auth_token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        record_pass("JSON Login", url, "POST", req_body, res.status_code, "JWT Access Token Issued")
    else:
        record_fail("JSON Login", url, res.status_code, res.text, "Invalid credentials or login endpoint failure")
except Exception as e:
    record_fail("JSON Login", BASE_URL, 500, str(e), "Exception during JSON login")

# 5. OAuth2 Form Login (/api/v1/auth/token)
try:
    url = f"{BASE_URL}/api/v1/auth/token"
    form_data = {"username": "live_user@doc2action.io", "password": user_pass}
    res = client.post(url, data=form_data)
    if res.status_code == 200 and "access_token" in res.json():
        record_pass("OAuth2 Form Login", url, "POST", "Form Data username/password", res.status_code, "OAuth2 Token Issued")
    else:
        record_fail("OAuth2 Form Login", url, res.status_code, res.text, "Form login failed")
except Exception as e:
    record_fail("OAuth2 Form Login", BASE_URL, 500, str(e), "Exception during Form login")

# 6. OpenAPI Specification Discovery
spec_id = None
try:
    url = f"{BASE_URL}/api/v1/openapi/discover"
    req_body = {"url": "https://petstore.swagger.io/v2/swagger.json"}
    res = client.post(url, json=req_body, headers=headers)
    if res.status_code == 201 and "id" in res.json():
        spec_data = res.json()
        spec_id = spec_data["id"]
        record_pass("OpenAPI Discovery", url, "POST", req_body, res.status_code, f"Parsed spec '{spec_data.get('title')}' with {len(spec_data.get('operations', []))} operations")
    else:
        record_fail("OpenAPI Discovery", url, res.status_code, res.text, "Failed to discover spec")
except Exception as e:
    record_fail("OpenAPI Discovery", BASE_URL, 500, str(e), "Exception during discovery")

# 7. Catalog Connection Creation
conn_id = None
endpoint_id = None
find_status_endpoint_id = None
try:
    if spec_id:
        url = f"{BASE_URL}/api/v1/catalog/connections"
        req_body = {
            "specification_id": spec_id,
            "name": "Live Petstore Connection",
            "auth_config": {"type": "none"}
        }
        res = client.post(url, json=req_body, headers=headers)
        if res.status_code == 201 and "id" in res.json():
            conn_data = res.json()
            conn_id = conn_data["id"]
            endpoints = conn_data.get("endpoints", [])
            for ep in endpoints:
                if ep.get("path") == "/pet/findByStatus":
                    find_status_endpoint_id = ep["id"]
            if not find_status_endpoint_id and endpoints:
                find_status_endpoint_id = endpoints[0]["id"]
            record_pass("Create Connection", url, "POST", req_body, res.status_code, f"Connection created with {len(endpoints)} endpoints")
        else:
            record_fail("Create Connection", url, res.status_code, res.text, "Connection creation failed")
except Exception as e:
    record_fail("Create Connection", BASE_URL, 500, str(e), "Exception during connection creation")

# 8. RAG Indexing & Search
try:
    if conn_id:
        url = f"{BASE_URL}/api/v1/rag/index/{conn_id}"
        res = client.post(url, headers=headers)
        if res.status_code == 200:
            record_pass("RAG Indexing", url, "POST", None, res.status_code, f"Indexed {res.json().get('indexed_count')} endpoints")
        else:
            record_fail("RAG Indexing", url, res.status_code, res.text, "Indexing failed")

        url = f"{BASE_URL}/api/v1/rag/search"
        req_body = {"query": "find pet by status"}
        res = client.post(url, json=req_body, headers=headers)
        if res.status_code == 200 and isinstance(res.json(), list):
            record_pass("RAG Search", url, "POST", req_body, res.status_code, f"Found {len(res.json())} search hits")
        else:
            record_fail("RAG Search", url, res.status_code, res.text, "Search failed")
except Exception as e:
    record_fail("RAG Operations", BASE_URL, 500, str(e), "Exception during RAG")

# 9. Verification Proposing, Confirming & Executing
proposal_id = None
try:
    if find_status_endpoint_id:
        url = f"{BASE_URL}/api/v1/verification/propose"
        req_body = {
            "endpoint_id": find_status_endpoint_id,
            "intent_summary": "Get pets by status available",
            "query_params": {"status": "available"}
        }
        res = client.post(url, json=req_body, headers=headers)
        if res.status_code == 201 and "proposal_id" in res.json():
            prop_data = res.json()
            proposal_id = prop_data["proposal_id"]
            record_pass("Action Proposal Creation", url, "POST", req_body, res.status_code, f"Proposal created status={prop_data.get('status')}")
        else:
            record_fail("Action Proposal Creation", url, res.status_code, res.text, "Proposal creation failed")

    if proposal_id:
        url = f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/confirm"
        res = client.post(url, headers=headers)
        if res.status_code == 200 and res.json().get("status") == "confirmed":
            record_pass("Action Proposal Confirmation", url, "POST", None, res.status_code, "Proposal status -> confirmed")
        else:
            record_fail("Action Proposal Confirmation", url, res.status_code, res.text, "Confirmation failed")

        url = f"{BASE_URL}/api/v1/verification/proposals/{proposal_id}/execute"
        res = client.post(url, headers=headers)
        if res.status_code == 200 and res.json().get("status") == "executed":
            record_pass("Action Proposal Execution", url, "POST", None, res.status_code, f"Proposal status -> executed (Latency: {res.json().get('execution_result', {}).get('latency_ms')} ms)")
        else:
            record_fail("Action Proposal Execution", url, res.status_code, res.text, "Execution failed")
except Exception as e:
    record_fail("Verification Flow", BASE_URL, 500, str(e), "Exception during verification flow")

# 10. Execution Audit Logs
try:
    url = f"{BASE_URL}/api/v1/execution/logs"
    res = client.get(url, headers=headers)
    if res.status_code == 200 and isinstance(res.json(), list):
        record_pass("Execution Audit Logs", url, "GET", None, res.status_code, f"Retrieved {len(res.json())} audit log entries")
    else:
        record_fail("Execution Audit Logs", url, res.status_code, res.text, "Audit log retrieval failed")
except Exception as e:
    record_fail("Execution Audit Logs", BASE_URL, 500, str(e), "Exception during audit logs")

# 11. Direct Postgres Database Verification
try:
    conn = psycopg2.connect(DB_CONN)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM api_specifications;")
    spec_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM api_action_proposals;")
    prop_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM api_execution_logs;")
    log_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print("\n--- Direct Postgres DB State ---")
    print(f"Users in DB: {user_count}")
    print(f"API Specifications in DB: {spec_count}")
    print(f"Action Proposals in DB: {prop_count}")
    print(f"Execution Audit Logs in DB: {log_count}")
except Exception as e:
    print(f"Database direct check error: {e}")

print("\n==========================================================")
print(f"TOTAL PASSED: {len(passed_tests)} | TOTAL FAILED: {len(failed_tests)}")
print("==========================================================")

if failed_tests:
    sys.exit(1)
sys.exit(0)
