import uuid
from typing import List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import BaseAppException
from app.modules.openapi.models import APISpecification, APIOperation, APISecurityScheme
from app.modules.openapi.parser import (
    parse_raw_spec_content,
    normalize_spec_metadata,
    extract_security_schemes,
    extract_operations,
)
from app.modules.openapi.ssrf import validate_url_against_ssrf


class FetchSpecException(BaseAppException):
    """Exception raised when fetching the remote OpenAPI specification fails."""

    def __init__(self, message: str = "Failed to fetch specification from URL") -> None:
        super().__init__(message=message, status_code=400)


def fetch_spec_from_url(url: str) -> str:
    """
    Validates URL against SSRF and fetches content safely.
    Handles redirect safety check by validating redirected URLs.
    """
    validated_url = validate_url_against_ssrf(url)

    try:
        with httpx.Client(timeout=10.0, follow_redirects=False) as client:
            response = client.get(validated_url)

            # Check redirect targets against SSRF
            redirect_count = 0
            while response.is_redirect and redirect_count < 3:
                redirect_count += 1
                location = response.headers.get("Location")
                if not location:
                    raise FetchSpecException("Redirect missing Location header")
                validated_url = validate_url_against_ssrf(location)
                response = client.get(validated_url)

            if response.status_code != 200:
                raise FetchSpecException(
                    f"Failed to retrieve specification: HTTP {response.status_code}"
                )

            return response.text
    except BaseAppException:
        raise
    except Exception as exc:
        raise FetchSpecException(f"Error fetching specification URL: {exc}")


def discover_and_store_spec(
    db: Session,
    owner_id: uuid.UUID,
    url: str,
    raw_content: Optional[str] = None,
) -> APISpecification:
    """
    Core discovery workflow:
    1. Fetch spec if raw_content not directly supplied (or validate URL against SSRF either way)
    2. Parse spec JSON/YAML
    3. Extract metadata, operations, security schemes
    4. Store in database
    """
    if not raw_content:
        raw_content = fetch_spec_from_url(url)
    else:
        # Validate URL even if raw_content was passed directly in test or upload
        validate_url_against_ssrf(url)

    spec_dict = parse_raw_spec_content(raw_content)
    title, version, spec_version, description, base_url, servers = normalize_spec_metadata(spec_dict)
    extracted_schemes = extract_security_schemes(spec_dict)
    extracted_ops = extract_operations(spec_dict)

    spec_record = APISpecification(
        owner_id=owner_id,
        title=title,
        description=description,
        version=version,
        spec_version=spec_version,
        source_url=url,
        base_url=base_url,
        servers=servers,
        raw_spec=spec_dict,
    )
    db.add(spec_record)
    db.flush()  # populate spec_record.id

    for scheme_data in extracted_schemes:
        scheme_obj = APISecurityScheme(
            specification_id=spec_record.id,
            scheme_name=scheme_data["scheme_name"],
            type=scheme_data["type"],
            scheme_in=scheme_data.get("scheme_in"),
            name=scheme_data.get("name"),
            scheme=scheme_data.get("scheme"),
            bearer_format=scheme_data.get("bearer_format"),
            details=scheme_data.get("details", {}),
        )
        db.add(scheme_obj)

    for op_data in extracted_ops:
        op_obj = APIOperation(
            specification_id=spec_record.id,
            operation_id=op_data.get("operation_id"),
            path=op_data["path"],
            method=op_data["method"],
            summary=op_data.get("summary"),
            description=op_data.get("description"),
            parameters=op_data.get("parameters", []),
            request_body=op_data.get("request_body"),
            responses=op_data.get("responses", {}),
            security=op_data.get("security", []),
        )
        db.add(op_obj)

    db.commit()
    db.refresh(spec_record)
    return spec_record


def get_specifications_by_owner(db: Session, owner_id: uuid.UUID) -> List[APISpecification]:
    """Retrieves all specifications discovered by a user."""
    return list(
        db.execute(
            select(APISpecification).where(APISpecification.owner_id == owner_id)
        ).scalars().all()
    )


def get_specification_by_id(
    db: Session, spec_id: uuid.UUID, owner_id: uuid.UUID
) -> Optional[APISpecification]:
    """Retrieves a single specification by ID for a user."""
    return db.execute(
        select(APISpecification).where(
            APISpecification.id == spec_id,
            APISpecification.owner_id == owner_id,
        )
    ).scalar_one_or_none()
