import sys
import json
import httpx

BASE_URL = "http://127.0.0.1:8000"

client = httpx.Client(timeout=10.0)

# Register/Login
login_payload = {"email": "gate_user@doc2action.io", "password": "GatePassword123!"}
res = client.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
token = res.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Discover petstore
res = client.post(f"{BASE_URL}/api/v1/openapi/discover", json={"url": "https://petstore.swagger.io/v2/swagger.json"}, headers=headers)
spec_id = res.json().get("id")

# Create Connection
res = client.post(f"{BASE_URL}/api/v1/catalog/connections", json={"specification_id": spec_id, "name": "Test Petstore", "auth_config": {"type": "none"}}, headers=headers)
conn_data = res.json()
endpoints = conn_data.get("endpoints", [])
print(f"Connection created. Endpoints count: {len(endpoints)}")
for ep in endpoints:
    print(f"EP ID: {ep.get('id')} | Method: {ep.get('method')} | Path: {ep.get('path')}")

ep_id = endpoints[0].get("id") if endpoints else None

# Propose
propose_payload = {
    "endpoint_id": ep_id,
    "intent_summary": "Test propose",
    "query_params": {"status": "available"}
}
res = client.post(f"{BASE_URL}/api/v1/verification/propose", json=propose_payload, headers=headers)
print("Propose status code:", res.status_code)
print("Propose response text:", res.text)
