# Doc2Action — Backend API Contract & Integration Specification

**API Version:** `0.1.0`  
**Base URL:** `http://localhost:8000/api/v1`  
**OpenAPI JSON Docs:** `http://localhost:8000/api/v1/openapi.json`  
**Interactive Swagger Docs:** `http://localhost:8000/api/v1/docs`  

---

## 1. Authentication Contract

All protected endpoints require HTTP Bearer authentication via standard JWT tokens.

### `POST /auth/register`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "Optional Name"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "Optional Name",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-08-30T00:00:00Z",
    "updated_at": "2026-08-30T00:00:00Z"
  }
  ```

### `POST /auth/login` (JSON Authentication)
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### `POST /auth/token` (Swagger Form Compatibility)
- **Form Data:** `username=user@example.com&password=securepassword123`
- **Response (200 OK):** Returns JWT token payload identical to `/auth/login`.

### `GET /auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Returns current user profile.

---

## 2. OpenAPI / Swagger Discovery Subsystem

### `POST /openapi/discover`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "url": "https://api.example.com/openapi.yaml"
  }
  ```
- **Behavior:** Validates target URL against SSRF (blocks local/private IP ranges), fetches spec, normalizes endpoints/security schemes, and persists to DB.
- **Response (201 Created):** Returns detailed specification object including extracted operations and security schemes.

### `GET /openapi/specifications`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Returns list of discovered specifications owned by current user.

### `GET /openapi/specifications/{spec_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Returns full detailed specification object.

---

## 3. Persistent API Catalog Subsystem

### `POST /catalog/connections`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "specification_id": "uuid-string",
    "name": "Custom Connection Name",
    "auth_config": {
      "type": "bearer",
      "token": "sk_test_..."
    }
  }
  ```
- **Response (201 Created):** Creates connection and extracts catalog `APIEndpoint` records.

### `GET /catalog/connections`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Lists user's active API connections.

### `GET /catalog/connections/{connection_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Connection details and catalog endpoints.

### `GET /catalog/connections/{connection_id}/endpoints`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Array of catalog endpoints for the connection.

### `DELETE /catalog/connections/{connection_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Deletes connection and cascades delete to endpoints.

---

## 4. RAG Knowledge Base & Semantic Search Subsystem

### `POST /rag/index/{connection_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Indexes connection catalog endpoints into vector store.

### `POST /rag/reindex/{connection_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Clears and re-indexes connection vectors.

### `DELETE /rag/index/{connection_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Deletes vector index for connection.

### `POST /rag/search`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "query": "process refund charge",
    "connection_id": "optional-uuid-string",
    "top_k": 5
  }
  ```
- **Response (200 OK):** Array of semantic endpoint matches formatted for LLM agent context.

---

## 5. Human-in-the-Loop Verification Subsystem

### `POST /verification/propose`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "endpoint_id": "uuid-string",
    "intent_summary": "Process refund for charge ch_123",
    "path_params": {},
    "query_params": {},
    "body": {"charge": "ch_123", "amount": 1000},
    "ttl_seconds": 300
  }
  ```
- **Response (201 Created):** Validates required parameters, constructs preview target URL, masks sensitive headers, and returns `status: "pending"` action proposal with `proposal_id`.

### `GET /verification/proposals`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Lists user's action proposals.

### `GET /verification/proposals/{proposal_id}`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Action proposal details and current status.

### `POST /verification/proposals/{proposal_id}/confirm`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Updates proposal status from `pending` to `confirmed`.

### `POST /verification/proposals/{proposal_id}/reject`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Updates proposal status to `rejected`.

### `POST /verification/proposals/{proposal_id}/execute`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Executes confirmed proposal, records latency and masked audit log, and returns execution result. Rejects unconfirmed, expired, or rejected proposals.

---

## 6. API Execution Engine & Audit Logs

### `POST /execution/preview`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:** Dry-run request preview without executing network requests.

### `POST /execution/execute`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:** Direct execution requiring `confirmed: true`.

### `GET /execution/logs`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Audit logs of executed API calls with masked authorization headers.
