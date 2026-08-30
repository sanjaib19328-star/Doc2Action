import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Natural language search query")
    connection_id: Optional[uuid.UUID] = Field(default=None, description="Optional connection filter")
    top_k: int = Field(default=5, ge=1, le=20)


class RAGSearchResult(BaseModel):
    endpoint_id: Optional[str] = None
    connection_id: Optional[str] = None
    connection_name: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    operation_id: Optional[str] = None
    base_url: Optional[str] = None
    score: float
    content: str


class RAGIndexResponse(BaseModel):
    message: str
    connection_id: uuid.UUID
    indexed_count: int


class RAGDeleteResponse(BaseModel):
    message: str
    connection_id: uuid.UUID
    deleted_count: int
