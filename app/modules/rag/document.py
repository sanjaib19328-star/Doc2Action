import json
import uuid
from typing import Any, Dict
from app.modules.catalog.models import APIConnection, APIEndpoint


def generate_endpoint_text_document(connection: APIConnection, endpoint: APIEndpoint) -> str:
    """
    Generates a rich, structured text document from a REAL catalog API endpoint.
    This document serves as the semantic payload for vector embeddings.
    """
    lines = [
        f"API Connection: {connection.name}",
        f"Base URL: {connection.base_url}",
        f"HTTP Method: {endpoint.method}",
        f"Path: {endpoint.path}",
    ]

    if endpoint.operation_id:
        lines.append(f"Operation ID: {endpoint.operation_id}")

    if endpoint.summary:
        lines.append(f"Summary: {endpoint.summary}")

    if endpoint.description:
        lines.append(f"Description: {endpoint.description}")

    if endpoint.parameters:
        lines.append(f"Parameters: {json.dumps(endpoint.parameters, default=str)}")

    if endpoint.request_body_schema:
        lines.append(f"Request Body Schema: {json.dumps(endpoint.request_body_schema, default=str)}")

    if endpoint.response_schema:
        lines.append(f"Response Schema: {json.dumps(endpoint.response_schema, default=str)}")

    if endpoint.security_requirements:
        lines.append(f"Security: {json.dumps(endpoint.security_requirements, default=str)}")

    return "\n".join(lines)


def generate_endpoint_metadata(
    owner_id: uuid.UUID,
    connection: APIConnection,
    endpoint: APIEndpoint,
) -> Dict[str, Any]:
    """
    Extracts structured metadata associated with each endpoint vector document.
    Enables strict user, connection, method, and path filtering.
    """
    return {
        "owner_id": str(owner_id),
        "connection_id": str(connection.id),
        "endpoint_id": str(endpoint.id),
        "operation_id": endpoint.operation_id or "",
        "method": endpoint.method.upper(),
        "path": endpoint.path,
        "base_url": connection.base_url,
        "connection_name": connection.name,
    }
