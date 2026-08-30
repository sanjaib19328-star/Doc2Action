from pydantic import BaseModel
from typing import Dict, Any, Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database_connected: bool
    details: Optional[Dict[str, Any]] = None
