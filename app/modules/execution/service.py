import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import BaseAppException
from app.modules.catalog.models import APIConnection, APIEndpoint
from app.modules.execution.builder import (
    validate_and_build_target_url,
    build_execution_headers,
    mask_sensitive_headers,
    ExecutionValidationException,
)
from app.modules.execution.models import APIExecutionLog
from app.modules.execution.schemas import (
    ExecutionPreviewRequest,
    ExecutionPreviewResponse,
    ExecutionExecuteRequest,
    ExecutionResponse,
)


class ExecutionException(BaseAppException):
    """Exception raised during API execution."""

    def __init__(self, message: str = "Execution failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


def get_user_catalog_endpoint(
    db: Session,
    owner_id: uuid.UUID,
    endpoint_id: uuid.UUID,
) -> Tuple[APIConnection, APIEndpoint]:
    """
    STRICT CATALOG VALIDATION:
    Retrieves the target APIEndpoint and parent APIConnection from the user's catalog.
    If endpoint does not exist in the user's registered catalog, access is strictly rejected.
    """
    result = db.execute(
        select(APIConnection, APIEndpoint)
        .join(APIEndpoint, APIConnection.id == APIEndpoint.connection_id)
        .where(
            APIEndpoint.id == endpoint_id,
            APIConnection.owner_id == owner_id,
        )
    ).first()

    if not result:
        raise ExecutionException(
            message="Endpoint not found in user's registered API catalog",
            status_code=404,
        )

    connection, endpoint = result
    return connection, endpoint


def preview_execution(
    db: Session,
    owner_id: uuid.UUID,
    req: ExecutionPreviewRequest,
) -> ExecutionPreviewResponse:
    """
    Generates an execution preview without making any network request.
    Allows human verification before execution.
    """
    connection, endpoint = get_user_catalog_endpoint(
        db=db, owner_id=owner_id, endpoint_id=req.endpoint_id
    )

    target_url = validate_and_build_target_url(
        connection=connection,
        endpoint=endpoint,
        path_params=req.path_params,
    )

    raw_headers = build_execution_headers(connection, req.headers)
    masked_headers = mask_sensitive_headers(raw_headers)

    return ExecutionPreviewResponse(
        endpoint_id=endpoint.id,
        connection_name=connection.name,
        method=endpoint.method.upper(),
        target_url=target_url,
        masked_headers=masked_headers,
        query_params=req.query_params,
        body=req.body,
        security_type=connection.auth_config.get("type"),
    )


def execute_api_call(
    db: Session,
    owner_id: uuid.UUID,
    req: ExecutionExecuteRequest,
    timeout_seconds: float = 10.0,
) -> ExecutionResponse:
    """
    Executes a catalog API request after human confirmation.
    Records masked logs, response metadata, latency, and status in the database.
    """
    if not req.confirmed:
        raise ExecutionException(
            message="Human confirmation required prior to execution. Set confirmed=True.",
            status_code=400,
        )

    connection, endpoint = get_user_catalog_endpoint(
        db=db, owner_id=owner_id, endpoint_id=req.endpoint_id
    )

    target_url = validate_and_build_target_url(
        connection=connection,
        endpoint=endpoint,
        path_params=req.path_params,
    )

    raw_headers = build_execution_headers(connection, req.headers)
    masked_headers = mask_sensitive_headers(raw_headers)

    start_time = time.time()
    status_code: Optional[int] = None
    exec_status = "success"
    response_data: Optional[Any] = None
    error_msg: Optional[str] = None

    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            res = client.request(
                method=endpoint.method.upper(),
                url=target_url,
                params=req.query_params,
                headers=raw_headers,
                json=req.body if req.body is not None else None,
            )
            status_code = res.status_code
            latency_ms = (time.time() - start_time) * 1000.0

            try:
                response_data = res.json()
            except Exception:
                response_data = res.text

            if status_code >= 400:
                exec_status = "error"
                error_msg = f"HTTP {status_code}: {res.reason_phrase}"

    except httpx.TimeoutException:
        latency_ms = (time.time() - start_time) * 1000.0
        exec_status = "timeout"
        error_msg = f"Request timed out after {timeout_seconds} seconds"
    except Exception as exc:
        latency_ms = (time.time() - start_time) * 1000.0
        exec_status = "failed"
        error_msg = f"Execution failed: {str(exc)}"

    # Record execution log in database with masked headers and application_id
    log_entry = APIExecutionLog(
        user_id=owner_id,
        connection_id=connection.id,
        endpoint_id=endpoint.id,
        application_id=connection.application_id,
        http_method=endpoint.method.upper(),
        target_url=target_url,
        request_headers=masked_headers,
        request_params=req.query_params,
        request_body=req.body,
        response_status_code=status_code,
        response_body=response_data,
        latency_ms=round(latency_ms, 2),
        status=exec_status,
        error_message=error_msg,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return ExecutionResponse(
        execution_id=log_entry.id,
        connection_id=connection.id,
        endpoint_id=endpoint.id,
        application_id=connection.application_id,
        method=endpoint.method.upper(),
        target_url=target_url,
        status_code=status_code,
        status=exec_status,
        latency_ms=round(latency_ms, 2),
        request_headers=masked_headers,
        request_params=req.query_params,
        request_body=req.body,
        response_body=response_data,
        error_message=error_msg,
        created_at=log_entry.created_at,
    )


def list_user_execution_logs(
    db: Session,
    owner_id: uuid.UUID,
    application_id: Optional[uuid.UUID] = None,
    limit: int = 50,
) -> List[APIExecutionLog]:
    """Retrieves execution audit logs for the authenticated user, optionally filtered by application_id."""
    stmt = select(APIExecutionLog).where(APIExecutionLog.user_id == owner_id)
    if application_id is not None:
        stmt = stmt.where(APIExecutionLog.application_id == application_id)
    stmt = stmt.order_by(APIExecutionLog.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
