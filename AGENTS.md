# AGENTS.md

## Strict Development Strategy
This repository (`Doc2Action`) is undergoing a clean, structured restart to eliminate past architectural coupling and frontend/backend mismatches.

### Execution Order (STRICT)
1. **PHASE 1: BACKEND (COMPLETE FIRST)**
   - Build and thoroughly test all backend API endpoints, database schemas, authentication contracts, OpenAPI discovery, RAG, and execution modules in isolation before touching frontend code.
2. **PHASE 2: FRONTEND (COMPLETE SECOND)**
   - Build React + Vite + TypeScript frontend matching the stabilized backend API contracts.
3. **PHASE 3: AI AGENT (COMPLETE THIRD)**
   - Implement LangGraph + Gemini AI agent workflows.
4. **PHASE 4: FULL INTEGRATION & DEPLOYMENT (FINAL)**
   - End-to-end integration, performance checks, and final deployment.

## Current Workspace Status
- The old implementation (`frontend/`, `backend/`, `examples/`) has been completely removed.
- Workspace is clean and prepared for **Backend Phase 1**.
- Do NOT create frontend or AI agent code until Backend Phase 1 is fully complete and verified.
