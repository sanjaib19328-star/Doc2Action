# Doc2Action — Backend Foundation (Phase 1)

Doc2Action is an AI Agent + OpenAPI RAG + API Execution platform. This repository contains the backend foundation built with FastAPI, PostgreSQL, SQLAlchemy, and Alembic.

## Prerequisites

- Python 3.10+
- PostgreSQL 12+

## Getting Started

### 1. Environment Setup

Clone the repository and navigate into the project directory:

```bash
cd Doc2Action
```

Create and activate a virtual environment:

```bash
python -m venv venv

# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# On Linux/macOS
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure your database credentials:

```bash
cp .env.example .env
```

Ensure your local PostgreSQL service is running and the database specified in `.env` exists.

### 4. Database Migrations

Run database migrations with Alembic:

```bash
alembic upgrade head
```

To generate a new migration after adding ORM models:

```bash
alembic revision --autogenerate -m "Migration description"
```

### 5. Running the API Server

Start the uvicorn development server:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be accessible at:
- **API Base**: `http://localhost:8000/api/v1`
- **Swagger Documentation**: `http://localhost:8000/api/v1/docs`
- **ReDoc Documentation**: `http://localhost:8000/api/v1/redoc`

### 6. Authentication API Endpoints

- **User Registration**: `POST http://localhost:8000/api/v1/auth/register` (JSON body)
- **User Login**: `POST http://localhost:8000/api/v1/auth/login` (JSON body)
- **OAuth2 Token**: `POST http://localhost:8000/api/v1/auth/token` (Form data, Swagger compatible)
- **Current User Profile**: `GET http://localhost:8000/api/v1/auth/me` (Bearer JWT auth)

### 6. Human-in-the-Loop Verification Endpoints

- **Propose API Action**: `POST http://localhost:8000/api/v1/verification/propose` (Validates parameters, builds target URL preview, creates pending proposal with TTL)
- **List Action Proposals**: `GET http://localhost:8000/api/v1/verification/proposals`
- **Get Action Proposal Details**: `GET http://localhost:8000/api/v1/verification/proposals/{proposal_id}`
- **Confirm Action Proposal**: `POST http://localhost:8000/api/v1/verification/proposals/{proposal_id}/confirm`
- **Reject Action Proposal**: `POST http://localhost:8000/api/v1/verification/proposals/{proposal_id}/reject`
- **Execute Confirmed Proposal**: `POST http://localhost:8000/api/v1/verification/proposals/{proposal_id}/execute`

### 7. API Execution Engine Endpoints

- **Preview Execution**: `POST http://localhost:8000/api/v1/execution/preview` (Validates path/query parameters, builds target URL, masks secrets)
- **Execute API Call**: `POST http://localhost:8000/api/v1/execution/execute` (Requires `confirmed: true`, performs request, records audit log)
- **Get Execution Logs**: `GET http://localhost:8000/api/v1/execution/logs`

### 7. RAG Knowledge Base & Semantic Search Endpoints

- **Index Connection Endpoints**: `POST http://localhost:8000/api/v1/rag/index/{connection_id}`
- **Re-index Connection Endpoints**: `POST http://localhost:8000/api/v1/rag/reindex/{connection_id}`
- **Delete Connection Index**: `DELETE http://localhost:8000/api/v1/rag/index/{connection_id}`
- **Semantic Search Catalog**: `POST http://localhost:8000/api/v1/rag/search` (JSON `{"query": "...", "top_k": 5}`)

### 7. Persistent API Catalog Endpoints

- **Create Connection & Extract Catalog**: `POST http://localhost:8000/api/v1/catalog/connections` (JSON `{"specification_id": "...", "name": "..."}`)
- **List Connections**: `GET http://localhost:8000/api/v1/catalog/connections`
- **Get Connection Details**: `GET http://localhost:8000/api/v1/catalog/connections/{connection_id}`
- **Get Catalog Endpoints**: `GET http://localhost:8000/api/v1/catalog/connections/{connection_id}/endpoints`
- **Delete Connection**: `DELETE http://localhost:8000/api/v1/catalog/connections/{connection_id}`

### 7. OpenAPI / Swagger Discovery Endpoints

- **Discover Specification**: `POST http://localhost:8000/api/v1/openapi/discover` (JSON `{"url": "..."}`)
- **List User Specifications**: `GET http://localhost:8000/api/v1/openapi/specifications` (Bearer JWT auth)
- **Get Specification Details**: `GET http://localhost:8000/api/v1/openapi/specifications/{spec_id}` (Bearer JWT auth)

### 7. Health Check Endpoints

- **Application Health**: `GET http://localhost:8000/api/v1/health`
- **Database Health**: `GET http://localhost:8000/api/v1/health/db`

### 8. Running Tests

Execute the backend test suite with pytest:

```bash
pytest
```

## Modular Project Architecture

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── health.py
│       └── router.py
├── core/
│   ├── config.py
│   ├── exceptions.py
│   ├── handlers.py
│   └── logging.py
├── db/
│   ├── base.py
│   └── session.py
├── modules/          # Future domain modules placeholders
│   ├── agent/
│   ├── api_connections/
│   ├── auth/
│   ├── catalog/
│   ├── execution/
│   ├── logs/
│   ├── openapi/
│   ├── rag/
│   └── verification/
├── schemas/
│   └── health.py
└── main.py
```
