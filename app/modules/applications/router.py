import uuid
from typing import List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.applications.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
)
from app.modules.applications.service import (
    create_application,
    get_application_by_id,
    list_user_applications,
    update_application,
    delete_application,
)

router = APIRouter()


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Application",
    description="Creates a new Application entity owned by the authenticated user.",
)
def handle_create_application(
    req: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = create_application(db=db, owner_id=current_user.id, req=req)
    return ApplicationResponse.model_validate(app)


@router.get(
    "",
    response_model=List[ApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Applications",
    description="Lists all Applications owned by the authenticated user.",
)
def handle_list_applications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ApplicationResponse]:
    apps = list_user_applications(db=db, owner_id=current_user.id)
    return [ApplicationResponse.model_validate(a) for a in apps]


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Application by ID",
    description="Retrieves application details enforcing strict user ownership.",
)
def handle_get_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = get_application_by_id(db=db, application_id=application_id, owner_id=current_user.id)
    return ApplicationResponse.model_validate(app)


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Application",
    description="Updates application name and description enforcing user ownership.",
)
def handle_update_application(
    application_id: uuid.UUID,
    req: ApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = update_application(db=db, application_id=application_id, owner_id=current_user.id, req=req)
    return ApplicationResponse.model_validate(app)


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Application",
    description="Deletes application enforcing user ownership.",
)
def handle_delete_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_application(db=db, application_id=application_id, owner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
