import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import BaseAppException
from app.db.base import Application
from app.modules.applications.schemas import ApplicationCreate, ApplicationUpdate


class ApplicationException(BaseAppException):
    def __init__(self, message: str = "Application operation failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


def create_application(
    db: Session,
    owner_id: uuid.UUID,
    req: ApplicationCreate,
) -> Application:
    app = Application(
        owner_id=owner_id,
        name=req.name.strip(),
        description=req.description.strip() if req.description else None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def get_application_by_id(
    db: Session,
    application_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> Application:
    app = db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.owner_id == owner_id,
        )
    ).scalar_one_or_none()

    if not app:
        raise ApplicationException(
            message="Application not found or access denied",
            status_code=404,
        )
    return app


def list_user_applications(
    db: Session,
    owner_id: uuid.UUID,
    limit: int = 100,
) -> List[Application]:
    return list(
        db.execute(
            select(Application)
            .where(Application.owner_id == owner_id)
            .order_by(Application.created_at.desc())
            .limit(limit)
        ).scalars().all()
    )


def update_application(
    db: Session,
    application_id: uuid.UUID,
    owner_id: uuid.UUID,
    req: ApplicationUpdate,
) -> Application:
    app = get_application_by_id(db, application_id=application_id, owner_id=owner_id)

    if req.name is not None:
        app.name = req.name.strip()
    if req.description is not None:
        app.description = req.description.strip() if req.description else None

    db.commit()
    db.refresh(app)
    return app


def delete_application(
    db: Session,
    application_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> None:
    app = get_application_by_id(db, application_id=application_id, owner_id=owner_id)
    db.delete(app)
    db.commit()
