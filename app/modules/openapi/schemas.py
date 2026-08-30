import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, HttpUrl


class DiscoverSpecRequest(BaseModel):
    url: str


class APIOperationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    operation_id: Optional[str] = None
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Any] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = {}
    security: List[Any] = []


class APISecuritySchemeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheme_name: str
    type: str
    scheme_in: Optional[str] = None
    name: Optional[str] = None
    scheme: Optional[str] = None
    bearer_format: Optional[str] = None
    details: Dict[str, Any] = {}


class APISpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: Optional[str] = None
    version: str
    spec_version: str
    source_url: str
    base_url: Optional[str] = None
    servers: List[Any] = []
    created_at: datetime
    updated_at: datetime


class APISpecificationDetailResponse(APISpecificationResponse):
    operations: List[APIOperationResponse] = []
    security_schemes: List[APISecuritySchemeResponse] = []
