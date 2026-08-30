import json
import yaml
from typing import Any, Dict, List, Tuple, Optional
from app.core.exceptions import BaseAppException


class InvalidSpecException(BaseAppException):
    """Exception raised when an OpenAPI/Swagger spec is malformed or invalid."""

    def __init__(self, message: str = "Invalid OpenAPI/Swagger specification") -> None:
        super().__init__(message=message, status_code=400)


def _json_serializable_converter(obj: Any) -> Any:
    """Recursively converts non-JSON-serializable objects (like datetime.date) to primitive strings/dicts."""
    if isinstance(obj, dict):
        return {k: _json_serializable_converter(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_json_serializable_converter(item) for item in obj]
    elif hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


def parse_raw_spec_content(content: str) -> Dict[str, Any]:
    """
    Detects and parses raw spec string as either JSON or YAML.
    """
    if not content or not content.strip():
        raise InvalidSpecException("Specification content is empty")

    content = content.strip()

    # Try JSON first if it looks like JSON
    if content.startswith("{") or content.startswith("["):
        try:
            parsed = json.loads(content)
            return _json_serializable_converter(parsed)
        except Exception as json_err:
            # Fallback to YAML parse
            try:
                parsed = yaml.safe_load(content)
                if isinstance(parsed, dict):
                    return _json_serializable_converter(parsed)
            except Exception:
                pass
            raise InvalidSpecException(f"Malformed JSON specification: {json_err}")

    # Otherwise try YAML
    try:
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            raise InvalidSpecException("Specification must be a JSON/YAML object")
        return _json_serializable_converter(parsed)
    except yaml.YAMLError as yaml_err:
        raise InvalidSpecException(f"Malformed YAML specification: {yaml_err}")


def normalize_spec_metadata(spec: Dict[str, Any]) -> Tuple[str, str, str, str, Optional[str], List[Dict[str, Any]]]:
    """
    Extracts metadata from spec:
    Returns (title, version, spec_version, description, base_url, servers)
    """
    if "openapi" in spec:
        spec_version = str(spec.get("openapi", "3.0.0"))
    elif "swagger" in spec:
        spec_version = str(spec.get("swagger", "2.0"))
    else:
        raise InvalidSpecException("Specification must contain 'openapi' or 'swagger' root field")

    info = spec.get("info")
    if not isinstance(info, dict):
        raise InvalidSpecException("Specification missing required 'info' object")

    title = info.get("title")
    if not title:
        raise InvalidSpecException("Specification info missing required 'title'")

    version = str(info.get("version", "1.0.0"))
    description = info.get("description")

    # Base URL & Servers extraction
    servers: List[Dict[str, Any]] = []
    base_url: Optional[str] = None

    if "servers" in spec and isinstance(spec["servers"], list) and len(spec["servers"]) > 0:
        # OpenAPI 3.x servers
        for s in spec["servers"]:
            if isinstance(s, dict) and "url" in s:
                servers.append({"url": s["url"], "description": s.get("description", "")})
        if servers:
            base_url = servers[0]["url"]
    elif "host" in spec:
        # Swagger 2.0 host + basePath + schemes
        host = spec.get("host", "")
        base_path = spec.get("basePath", "")
        schemes = spec.get("schemes", ["https"])
        scheme = schemes[0] if isinstance(schemes, list) and schemes else "https"
        computed_url = f"{scheme}://{host}{base_path}".rstrip("/")
        base_url = computed_url
        servers.append({"url": computed_url, "description": "Default Swagger 2.0 host"})

    return title, version, spec_version, description or "", base_url, servers


def extract_security_schemes(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts security scheme definitions from OpenAPI 3.x or Swagger 2.0.
    """
    extracted = []

    # OpenAPI 3.x: components.securitySchemes
    if "components" in spec and isinstance(spec["components"], dict):
        schemes = spec["components"].get("securitySchemes", {})
        if isinstance(schemes, dict):
            for scheme_name, scheme_def in schemes.items():
                if isinstance(scheme_def, dict):
                    extracted.append({
                        "scheme_name": scheme_name,
                        "type": scheme_def.get("type", "unknown"),
                        "scheme_in": scheme_def.get("in"),
                        "name": scheme_def.get("name"),
                        "scheme": scheme_def.get("scheme"),
                        "bearer_format": scheme_def.get("bearerFormat"),
                        "details": scheme_def,
                    })

    # Swagger 2.0: securityDefinitions
    elif "securityDefinitions" in spec and isinstance(spec["securityDefinitions"], dict):
        schemes = spec["securityDefinitions"]
        for scheme_name, scheme_def in schemes.items():
            if isinstance(scheme_def, dict):
                extracted.append({
                    "scheme_name": scheme_name,
                    "type": scheme_def.get("type", "unknown"),
                    "scheme_in": scheme_def.get("in"),
                    "name": scheme_def.get("name"),
                    "scheme": None,
                    "bearer_format": None,
                    "details": scheme_def,
                })

    return extracted


def extract_operations(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts normalized HTTP operations (paths, methods, params, requestBody, responses, security).
    """
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        raise InvalidSpecException("Specification missing required 'paths' object")

    operations = []
    http_methods = {"get", "post", "put", "delete", "patch", "options", "head"}

    # Common parameters at path level
    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_common_params = path_item.get("parameters", [])
        if not isinstance(path_common_params, list):
            path_common_params = []

        for method, op_data in path_item.items():
            if method.lower() not in http_methods or not isinstance(op_data, dict):
                continue

            op_params = op_data.get("parameters", [])
            if not isinstance(op_params, list):
                op_params = []

            combined_params = path_common_params + op_params

            # Handle OpenAPI 3.x requestBody vs Swagger 2.0 body parameter
            request_body = op_data.get("requestBody")
            if not request_body:
                # Check for Swagger 2.0 body parameter
                body_params = [p for p in combined_params if isinstance(p, dict) and p.get("in") == "body"]
                if body_params:
                    request_body = {
                        "description": body_params[0].get("description"),
                        "required": body_params[0].get("required", False),
                        "schema": body_params[0].get("schema"),
                    }

            operations.append({
                "operation_id": op_data.get("operationId"),
                "path": path_str,
                "method": method.upper(),
                "summary": op_data.get("summary"),
                "description": op_data.get("description"),
                "parameters": combined_params,
                "request_body": request_body,
                "responses": op_data.get("responses", {}),
                "security": op_data.get("security", spec.get("security", [])),
            })

    return operations
