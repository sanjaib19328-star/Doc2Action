import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.rag.schemas import (
    RAGSearchRequest,
    RAGSearchResult,
    RAGIndexResponse,
    RAGDeleteResponse,
)
from app.modules.rag import service

router = APIRouter()


@router.post(
    "/index/{connection_id}",
    response_model=RAGIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Index API Connection Catalog Endpoints into Vector Store",
    description="Generates rich documents for catalog endpoints and indexes them into the vector store.",
)
def index_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RAGIndexResponse:
    count = service.index_connection_endpoints(
        db=db, owner_id=current_user.id, connection_id=connection_id
    )
    return RAGIndexResponse(
        message="Successfully indexed API connection endpoints",
        connection_id=connection_id,
        indexed_count=count,
    )


@router.post(
    "/reindex/{connection_id}",
    response_model=RAGIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-index API Connection Catalog Endpoints",
    description="Clears existing vector index for connection and re-indexes all endpoints.",
)
def reindex_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RAGIndexResponse:
    count = service.reindex_connection_endpoints(
        db=db, owner_id=current_user.id, connection_id=connection_id
    )
    return RAGIndexResponse(
        message="Successfully re-indexed API connection endpoints",
        connection_id=connection_id,
        indexed_count=count,
    )


@router.delete(
    "/index/{connection_id}",
    response_model=RAGDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete API Connection Index",
    description="Removes all vectors associated with an API connection.",
)
def delete_index(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
) -> RAGDeleteResponse:
    count = service.delete_connection_index(
        owner_id=current_user.id, connection_id=connection_id
    )
    return RAGDeleteResponse(
        message="Successfully deleted vector index for connection",
        connection_id=connection_id,
        deleted_count=count,
    )


@router.post(
    "/search",
    response_model=List[RAGSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Semantic Search API Catalog",
    description="Performs vector similarity search across indexed API endpoints for the user.",
)
def search_catalog(
    search_in: RAGSearchRequest,
    current_user: User = Depends(get_current_active_user),
) -> List[RAGSearchResult]:
    results = service.semantic_search_catalog(
        owner_id=current_user.id,
        query=search_in.query,
        connection_id=search_in.connection_id,
        top_k=search_in.top_k,
    )
    return results
