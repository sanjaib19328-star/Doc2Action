import httpx

client = httpx.Client(timeout=5.0)
base = "http://127.0.0.1:8000/api/v1"

# 1. Invalid Login
res = client.post(f"{base}/auth/login", json={"email": "wrong@doc2action.io", "password": "wrong"})
print("1. Invalid Login status:", res.status_code, "| detail:", res.json().get("detail"))

# 2. Unauthorized request
res = client.get(f"{base}/auth/me")
print("2. Unauthorized status:", res.status_code, "| detail:", res.json().get("detail"))

# Login for token
res = client.post(f"{base}/auth/login", json={"email": "gate_user@doc2action.io", "password": "GatePassword123!"})
headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

# 3. Nonexistent Connection ID
res = client.get(f"{base}/catalog/connections/00000000-0000-0000-0000-000000000000", headers=headers)
print("3. Nonexistent connection status:", res.status_code, "| detail:", res.json().get("detail"))

# 4. SSRF invalid URL attempt
res = client.post(f"{base}/openapi/discover", json={"url": "http://127.0.0.1:8000/admin"}, headers=headers)
print("4. SSRF Discovery status:", res.status_code, "| detail:", res.json().get("detail"))
