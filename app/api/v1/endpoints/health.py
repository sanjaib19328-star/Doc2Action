from fastapi import APIRouter, status, Response
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse, DatabaseHealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Returns the overall status of the API service.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Database Health Check",
    description="Verifies database connectivity and returns connection status.",
)
async def db_health_check(response: Response) -> DatabaseHealthResponse:
    is_connected = check_db_connection()
    if not is_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(
            status="unhealthy",
            database_connected=False,
            details={"error": "Unable to connect to PostgreSQL database"},
        )

    return DatabaseHealthResponse(
        status="healthy",
        database_connected=True,
    )
