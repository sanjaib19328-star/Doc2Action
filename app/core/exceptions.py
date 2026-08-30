from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base exception for all custom application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DatabaseException(BaseAppException):
    """Exception raised for database operations failures."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=500, details=details)


class ResourceNotFoundException(BaseAppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=404, details=details)
