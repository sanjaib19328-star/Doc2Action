import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.openapi.schemas import (
    DiscoverSpecRequest,
    APISpecificationResponse,
    APISpecificationDetailResponse,
)
from app.modules.openapi import service

router = APIRouter()


@router.post(
    "/discover",
    response_model=APISpecificationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Discover & Ingest OpenAPI/Swagger Specification",
    description="Validates target URL against SSRF, verifies application ownership if application_id is provided, fetches spec, and stores in database.",
)
def discover_specification(
    request: DiscoverSpecRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APISpecificationDetailResponse:
    if not request.url or not request.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required URL parameter",
        )
    spec_record = service.discover_and_store_spec(
        db=db,
        owner_id=current_user.id,
        url=request.url.strip(),
        application_id=request.application_id,
    )
    return spec_record


@router.get(
    "/specifications",
    response_model=List[APISpecificationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Discovered Specifications",
    description="Retrieves all discovered API specifications for the current user, optionally filtered by application_id.",
)
def list_specifications(
    application_id: Optional[uuid.UUID] = Query(None, description="Optional application ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[APISpecificationResponse]:
    return service.get_specifications_by_owner(
        db=db, owner_id=current_user.id, application_id=application_id
    )


@router.get(
    "/specifications/{spec_id}",
    response_model=APISpecificationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specification Details",
    description="Retrieves detailed specification with normalized operations and security schemes.",
)
def get_specification(
    spec_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APISpecificationDetailResponse:
    spec_record = service.get_specification_by_id(
        db=db, spec_id=spec_id, owner_id=current_user.id
    )
    if not spec_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found",
        )
    return spec_record
