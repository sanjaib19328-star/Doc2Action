from typing import Any, Dict, Tuple
from urllib.parse import quote
from app.core.exceptions import BaseAppException
from app.modules.catalog.models import APIConnection, APIEndpoint


class ExecutionValidationException(BaseAppException):
    """Exception raised when API execution validation fails."""

    def __init__(self, message: str = "Execution validation failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


SENSITIVE_HEADER_KEYS = {"authorization", "api-key", "x-api-key", "secret", "token", "password"}


def mask_sensitive_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Masks sensitive values in headers to ensure secrets are never leaked into logs.
    """
    masked = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADER_KEYS:
            if len(v) > 8:
                masked[k] = f"{v[:4]}...{v[-4:]}"
            else:
                masked[k] = "******"
        else:
            masked[k] = v
    return masked


def validate_and_build_target_url(
    connection: APIConnection,
    endpoint: APIEndpoint,
    path_params: Dict[str, Any],
) -> str:
    """
    Validates required path parameters and constructs the formatted target URL.
    Replaces {param} placeholders in path.
    """
    base_url = connection.base_url.rstrip("/")
    path = endpoint.path

    # Extract declared required path parameters from endpoint spec
    declared_path_params = [
        p.get("name") for p in endpoint.parameters if isinstance(p, dict) and p.get("in") == "path"
    ]

    for param_name in declared_path_params:
        if param_name not in path_params or path_params[param_name] is None:
            raise ExecutionValidationException(
                f"Missing required path parameter: '{param_name}'"
            )

    # Format path
    formatted_path = path
    for param_name, param_val in path_params.items():
        placeholder = f"{{{param_name}}}"
        if placeholder in formatted_path:
            formatted_path = formatted_path.replace(placeholder, quote(str(param_val)))

    return f"{base_url}/{formatted_path.lstrip('/')}"


def build_execution_headers(
    connection: APIConnection,
    user_headers: Dict[str, str],
) -> Dict[str, str]:
    """
    Combines connection authentication configuration headers with user-provided headers.
    """
    headers = {"User-Agent": "Doc2Action-ExecutionEngine/1.0"}

    # Apply auth_config from connection if configured
    auth_config = connection.auth_config or {}
    auth_type = auth_config.get("type", "").lower()

    if auth_type == "bearer" and "token" in auth_config:
        headers["Authorization"] = f"Bearer {auth_config['token']}"
    elif auth_type == "api_key":
        header_name = auth_config.get("key_name", "X-API-Key")
        key_value = auth_config.get("key_value", "")
        if auth_config.get("key_in", "header") == "header":
            headers[header_name] = key_value

    # Override/add user headers
    headers.update(user_headers)
    return headers
