import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.catalog.schemas import (
    APIConnectionCreate,
    APIConnectionResponse,
    APIConnectionDetailResponse,
    APIEndpointResponse,
)
from app.modules.catalog import service

router = APIRouter()


@router.post(
    "/connections",
    response_model=APIConnectionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Connection from Discovered Specification",
    description="Connects an ingested API specification and populates the API catalog endpoints, associated with an application.",
)
def create_connection(
    conn_in: APIConnectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APIConnectionDetailResponse:
    connection = service.create_connection_from_spec(
        db=db, owner_id=current_user.id, conn_in=conn_in
    )
    return connection


@router.get(
    "/connections",
    response_model=List[APIConnectionResponse],
    status_code=status.HTTP_200_OK,
    summary="List User API Connections",
    description="Retrieves all API connections belonging to the authenticated user, optionally filtered by application_id.",
)
def list_connections(
    application_id: Optional[uuid.UUID] = Query(None, description="Optional application ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[APIConnectionResponse]:
    return service.list_connections(
        db=db, owner_id=current_user.id, application_id=application_id
    )


@router.get(
    "/connections/{connection_id}",
    response_model=APIConnectionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API Connection Details",
    description="Retrieves details and catalog endpoints for an API connection.",
)
def get_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APIConnectionDetailResponse:
    connection = service.get_connection_by_id(
        db=db, connection_id=connection_id, owner_id=current_user.id
    )
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Connection not found or access denied",
        )
    return connection


@router.get(
    "/connections/{connection_id}/endpoints",
    response_model=List[APIEndpointResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Connection Endpoints",
    description="Retrieves all catalog endpoints for an API connection.",
)
def get_connection_endpoints(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[APIEndpointResponse]:
    return service.get_connection_endpoints(
        db=db, connection_id=connection_id, owner_id=current_user.id
    )


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete API Connection",
    description="Deletes an API connection and its associated catalog endpoints.",
)
def delete_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service.delete_connection(
        db=db, connection_id=connection_id, owner_id=current_user.id
    )
    return {"message": "API Connection deleted successfully", "id": str(connection_id)}
