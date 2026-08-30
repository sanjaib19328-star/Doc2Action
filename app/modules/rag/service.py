import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.exceptions import BaseAppException
from app.modules.catalog.service import get_connection_by_id, get_connection_endpoints
from app.modules.rag.document import (
    generate_endpoint_text_document,
    generate_endpoint_metadata,
)
from app.modules.rag.vector_store import (
    vector_store_instance,
    embedding_provider_instance,
    VectorServiceException,
)


class RAGException(BaseAppException):
    """Exception raised for RAG service errors."""

    def __init__(self, message: str = "RAG operation failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


def index_connection_endpoints(
    db: Session,
    owner_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> int:
    """
    Indexes all catalog endpoints for a specific API connection into the vector store.
    Enforces user ownership on connection.
    """
    connection = get_connection_by_id(db, connection_id=connection_id, owner_id=owner_id)
    if not connection:
        raise RAGException(message="Connection not found or access denied", status_code=404)

    endpoints = get_connection_endpoints(db, connection_id=connection_id, owner_id=owner_id)
    if not endpoints:
        return 0

    documents_to_upsert = []
    for ep in endpoints:
        text_doc = generate_endpoint_text_document(connection, ep)
        metadata = generate_endpoint_metadata(owner_id, connection, ep)
        vector = embedding_provider_instance.embed_text(text_doc)

        documents_to_upsert.append({
            "doc_id": str(ep.id),
            "content": text_doc,
            "metadata": metadata,
            "vector": vector,
        })

    vector_store_instance.upsert_documents(documents_to_upsert)
    return len(documents_to_upsert)


def reindex_connection_endpoints(
    db: Session,
    owner_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> int:
    """
    Deletes existing vectors for an API connection and re-indexes them fresh.
    """
    delete_connection_index(owner_id=owner_id, connection_id=connection_id)
    return index_connection_endpoints(db=db, owner_id=owner_id, connection_id=connection_id)


def delete_connection_index(
    owner_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> int:
    """
    Deletes all vector documents matching connection_id and owner_id.
    """
    filters = {
        "owner_id": str(owner_id),
        "connection_id": str(connection_id),
    }
    return vector_store_instance.delete_by_filter(filters)


def semantic_search_catalog(
    owner_id: uuid.UUID,
    query: str,
    application_id: Optional[uuid.UUID] = None,
    connection_id: Optional[uuid.UUID] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Executes semantic search over indexed API endpoints for the authenticated user.
    Optionally filters by application_id and/or connection_id.
    """
    if not query or not query.strip():
        raise RAGException(message="Search query cannot be empty", status_code=400)

    query_vector = embedding_provider_instance.embed_text(query.strip())

    filters: Dict[str, Any] = {"owner_id": str(owner_id)}
    if application_id:
        filters["application_id"] = str(application_id)
    if connection_id:
        filters["connection_id"] = str(connection_id)

    raw_results = vector_store_instance.search(
        query_vector=query_vector,
        top_k=top_k,
        filters=filters,
    )

    search_results = []
    for res in raw_results:
        meta = res["metadata"]
        search_results.append({
            "endpoint_id": meta.get("endpoint_id"),
            "connection_id": meta.get("connection_id"),
            "application_id": meta.get("application_id"),
            "connection_name": meta.get("connection_name"),
            "method": meta.get("method"),
            "path": meta.get("path"),
            "operation_id": meta.get("operation_id"),
            "base_url": meta.get("base_url"),
            "score": res["score"],
            "content": res["content"],
        })

    return search_results
