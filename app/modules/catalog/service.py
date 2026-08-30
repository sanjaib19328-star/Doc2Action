import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import BaseAppException
from app.db.base import Application
from app.modules.catalog.models import APIConnection, APIEndpoint
from app.modules.catalog.schemas import APIConnectionCreate
from app.modules.openapi.models import APISpecification


class CatalogException(BaseAppException):
    """Exception raised for API catalog errors."""

    def __init__(self, message: str = "Catalog operation failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


def create_connection_from_spec(
    db: Session,
    owner_id: uuid.UUID,
    conn_in: APIConnectionCreate,
) -> APIConnection:
    """
    Creates an APIConnection from an ingested APISpecification and extracts all endpoints into APIEndpoint catalog.
    Enforces user ownership and application match validation.
    """
    spec = db.execute(
        select(APISpecification).where(
            APISpecification.id == conn_in.specification_id,
            APISpecification.owner_id == owner_id,
        )
    ).scalar_one_or_none()

    if not spec:
        raise CatalogException(
            message="Specification not found or access denied", status_code=404
        )

    # Determine effective application_id
    effective_app_id = conn_in.application_id or spec.application_id

    # If an application_id was explicitly supplied, verify user ownership
    if conn_in.application_id is not None:
        app_record = db.execute(
            select(Application).where(
                Application.id == conn_in.application_id,
                Application.owner_id == owner_id,
            )
        ).scalar_one_or_none()
        if not app_record:
            raise CatalogException(
                message="Application not found or access denied", status_code=404
            )

    # Validate application match: if spec belongs to Application A, connection cannot claim Application B
    if spec.application_id is not None and conn_in.application_id is not None:
        if spec.application_id != conn_in.application_id:
            raise CatalogException(
                message=f"Mismatched application: Specification belongs to Application {spec.application_id}, but connection requested Application {conn_in.application_id}",
                status_code=400,
            )

    effective_name = conn_in.name or spec.title
    effective_base_url = conn_in.base_url or spec.base_url or "https://api.example.com"

    connection = APIConnection(
        owner_id=owner_id,
        specification_id=spec.id,
        application_id=effective_app_id,
        name=effective_name,
        base_url=effective_base_url,
        is_active=True,
        auth_config=conn_in.auth_config,
    )
    db.add(connection)
    db.flush()  # Populate connection.id

    # Create catalog endpoints from spec operations
    for op in spec.operations:
        endpoint = APIEndpoint(
            connection_id=connection.id,
            operation_id=op.operation_id,
            method=op.method,
            path=op.path,
            summary=op.summary,
            description=op.description,
            parameters=op.parameters,
            request_body_schema=op.request_body,
            response_schema=op.responses,
            security_requirements=op.security,
        )
        db.add(endpoint)

    db.commit()
    db.refresh(connection)
    return connection


def list_connections(
    db: Session,
    owner_id: uuid.UUID,
    application_id: Optional[uuid.UUID] = None,
) -> List[APIConnection]:
    """Lists all API connections owned by the specified user, optionally filtered by application_id."""
    stmt = select(APIConnection).where(APIConnection.owner_id == owner_id)
    if application_id is not None:
        stmt = stmt.where(APIConnection.application_id == application_id)
    return list(db.execute(stmt).scalars().all())


def get_connection_by_id(
    db: Session, connection_id: uuid.UUID, owner_id: uuid.UUID
) -> Optional[APIConnection]:
    """Retrieves a single API connection by ID enforcing owner isolation."""
    return db.execute(
        select(APIConnection).where(
            APIConnection.id == connection_id,
            APIConnection.owner_id == owner_id,
        )
    ).scalar_one_or_none()


def get_connection_endpoints(
    db: Session, connection_id: uuid.UUID, owner_id: uuid.UUID
) -> List[APIEndpoint]:
    """Retrieves all catalog endpoints for a connection, enforcing owner isolation."""
    connection = get_connection_by_id(db, connection_id=connection_id, owner_id=owner_id)
    if not connection:
        raise CatalogException(message="Connection not found or access denied", status_code=404)
    return list(
        db.execute(
            select(APIEndpoint).where(APIEndpoint.connection_id == connection_id)
        ).scalars().all()
    )


def delete_connection(
    db: Session, connection_id: uuid.UUID, owner_id: uuid.UUID
) -> bool:
    """Deletes an API connection and its associated catalog endpoints enforcing owner isolation."""
    connection = get_connection_by_id(db, connection_id=connection_id, owner_id=owner_id)
    if not connection:
        raise CatalogException(message="Connection not found or access denied", status_code=404)

    db.delete(connection)
    db.commit()
    return True
