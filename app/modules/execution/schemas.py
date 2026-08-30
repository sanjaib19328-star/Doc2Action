import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExecutionPreviewRequest(BaseModel):
    endpoint_id: uuid.UUID
    path_params: Dict[str, Any] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None


class ExecutionPreviewResponse(BaseModel):
    endpoint_id: uuid.UUID
    connection_name: str
    method: str
    target_url: str
    masked_headers: Dict[str, str]
    query_params: Dict[str, Any]
    body: Optional[Any] = None
    security_type: Optional[str] = None


class ExecutionExecuteRequest(ExecutionPreviewRequest):
    confirmed: bool = Field(
        default=False,
        description="Explicit human confirmation flag required for real execution.",
    )


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    execution_id: uuid.UUID
    connection_id: uuid.UUID
    endpoint_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    method: str
    target_url: str
    status_code: Optional[int] = None
    status: str  # success, error, timeout, failed
    latency_ms: float
    request_headers: Dict[str, str]
    request_params: Dict[str, Any]
    request_body: Optional[Any] = None
    response_body: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime
