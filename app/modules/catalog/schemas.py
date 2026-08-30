import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class APIConnectionCreate(BaseModel):
    specification_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    base_url: Optional[str] = None
    auth_config: Dict[str, Any] = {}


class APIEndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connection_id: uuid.UUID
    operation_id: Optional[str] = None
    method: str
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Any] = []
    request_body_schema: Optional[Dict[str, Any]] = None
    response_schema: Dict[str, Any] = {}
    security_requirements: List[Any] = []
    created_at: datetime
    updated_at: datetime


class APIConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    specification_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    name: str
    base_url: str
    is_active: bool
    auth_config: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class APIConnectionDetailResponse(APIConnectionResponse):
    endpoints: List[APIEndpointResponse] = []
