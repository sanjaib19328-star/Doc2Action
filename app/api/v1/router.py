from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.modules.auth.router import router as auth_router
from app.modules.openapi.router import router as openapi_router
from app.modules.catalog.router import router as catalog_router
from app.modules.rag.router import router as rag_router
from app.modules.execution.router import router as execution_router
from app.modules.verification.router import router as verification_router
from app.modules.agent.router import router as agent_router
from app.modules.applications.router import router as applications_router

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(openapi_router, prefix="/openapi", tags=["OpenAPI Discovery"])
api_router.include_router(catalog_router, prefix="/catalog", tags=["API Catalog"])
api_router.include_router(rag_router, prefix="/rag", tags=["RAG & Knowledge Base"])
api_router.include_router(execution_router, prefix="/execution", tags=["API Execution Engine"])
api_router.include_router(verification_router, prefix="/verification", tags=["Human-in-the-Loop Verification"])
api_router.include_router(agent_router, prefix="/agent", tags=["AI Agent Workflow"])
api_router.include_router(applications_router, prefix="/applications", tags=["Applications"])
