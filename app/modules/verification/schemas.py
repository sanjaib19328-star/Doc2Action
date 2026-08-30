import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CreateActionProposalRequest(BaseModel):
    endpoint_id: uuid.UUID
    application_id: Optional[uuid.UUID] = Field(default=None, description="Optional application ID context")
    intent_summary: str = Field(min_length=1, description="Description of expected operation")
    path_params: Dict[str, Any] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None
    ttl_seconds: int = Field(default=300, ge=30, le=3600, description="Proposal time-to-live in seconds")


class ActionProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    proposal_id: uuid.UUID
    user_id: uuid.UUID
    connection_id: uuid.UUID
    endpoint_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    intent_summary: str
    http_method: str
    target_url: str
    path_params: Dict[str, Any]
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    body: Optional[Any] = None
    status: str  # pending, confirmed, rejected, executed, expired
    expires_at: datetime
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime


class RejectProposalRequest(BaseModel):
    reason: Optional[str] = "User rejected proposal"
