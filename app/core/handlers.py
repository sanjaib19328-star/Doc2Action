from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import BaseAppException
from app.core.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers for the FastAPI application.
    """

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        logger.warning(f"App Exception [{exc.status_code}]: {exc.message} - path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "details": exc.details,
                    "type": exc.__class__.__name__,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning(f"HTTP Exception [{exc.status_code}]: {exc.detail} - path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": str(exc.detail),
                    "type": "HTTPException",
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Validation Exception: {exc.errors()} - path: {request.url.path}")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "message": "Validation Error",
                    "details": exc.errors(),
                    "type": "RequestValidationError",
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled Exception: {str(exc)} - path: {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "An internal server error occurred.",
                    "type": "InternalServerError",
                }
            },
        )
