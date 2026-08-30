import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.execution.schemas import (
    ExecutionPreviewRequest,
    ExecutionPreviewResponse,
    ExecutionExecuteRequest,
    ExecutionResponse,
)
from app.modules.execution import service

router = APIRouter()


@router.post(
    "/preview",
    response_model=ExecutionPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview API Execution Request",
    description="Validates catalog endpoint and constructs target URL and masked headers without executing.",
)
def preview_execution(
    req: ExecutionPreviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ExecutionPreviewResponse:
    return service.preview_execution(db=db, owner_id=current_user.id, req=req)


@router.post(
    "/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Catalog API Request",
    description="Validates catalog existence, requires human confirmation, executes request, and logs result.",
)
def execute_request(
    req: ExecutionExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ExecutionResponse:
    return service.execute_api_call(db=db, owner_id=current_user.id, req=req)


@router.get(
    "/logs",
    response_model=List[ExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User API Execution Logs",
    description="Retrieves masked audit logs for executed API calls for the user, optionally filtered by application_id.",
)
def get_execution_logs(
    application_id: Optional[uuid.UUID] = Query(None, description="Optional application ID filter"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ExecutionResponse]:
    logs = service.list_user_execution_logs(
        db=db, owner_id=current_user.id, application_id=application_id, limit=limit
    )
    
    # Map ORM logs to response schema
    results = []
    for log in logs:
        results.append(
            ExecutionResponse(
                execution_id=log.id,
                connection_id=log.connection_id,
                endpoint_id=log.endpoint_id,
                application_id=log.application_id,
                method=log.http_method,
                target_url=log.target_url,
                status_code=log.response_status_code,
                status=log.status,
                latency_ms=log.latency_ms,
                request_headers=log.request_headers,
                request_params=log.request_params,
                request_body=log.request_body,
                response_body=log.response_body,
                error_message=log.error_message,
                created_at=log.created_at,
            )
        )
    return results
