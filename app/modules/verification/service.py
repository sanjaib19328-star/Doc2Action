import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import BaseAppException
from app.modules.execution.builder import (
    validate_and_build_target_url,
    mask_sensitive_headers,
    build_execution_headers,
)
from app.modules.execution.service import (
    get_user_catalog_endpoint,
    execute_api_call,
)
from app.modules.execution.schemas import ExecutionExecuteRequest
from app.modules.verification.models import APIActionProposal
from app.modules.verification.schemas import (
    CreateActionProposalRequest,
    ActionProposalResponse,
)


class VerificationException(BaseAppException):
    """Exception raised for human verification workflow errors."""

    def __init__(self, message: str = "Verification error", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


def create_proposal(
    db: Session,
    owner_id: uuid.UUID,
    req: CreateActionProposalRequest,
) -> APIActionProposal:
    """
    PROPOSE & VALIDATE:
    1. Validates endpoint exists in user's registered catalog.
    2. Validates parameters and constructs target URL.
    3. Masks sensitive headers.
    4. Creates a pending proposal with expiration timestamp.
    """
    connection, endpoint = get_user_catalog_endpoint(
        db=db, owner_id=owner_id, endpoint_id=req.endpoint_id
    )

    target_url = validate_and_build_target_url(
        connection=connection,
        endpoint=endpoint,
        path_params=req.path_params,
    )

    raw_headers = build_execution_headers(connection, req.headers)
    masked_headers = mask_sensitive_headers(raw_headers)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=req.ttl_seconds)

    proposal = APIActionProposal(
        user_id=owner_id,
        connection_id=connection.id,
        endpoint_id=endpoint.id,
        intent_summary=req.intent_summary,
        http_method=endpoint.method.upper(),
        target_url=target_url,
        path_params=req.path_params,
        query_params=req.query_params,
        headers=masked_headers,
        body=req.body,
        status="pending",
        expires_at=expires_at,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def get_proposal_by_id(
    db: Session,
    proposal_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> APIActionProposal:
    """
    Retrieves proposal by ID enforcing user isolation and checking expiration.
    """
    proposal = db.execute(
        select(APIActionProposal).where(
            APIActionProposal.id == proposal_id,
            APIActionProposal.user_id == owner_id,
        )
    ).scalar_one_or_none()

    if not proposal:
        raise VerificationException(
            message="Action proposal not found or access denied",
            status_code=404,
        )

    # Auto-expire if pending and past expiration time
    expires_at = (
        proposal.expires_at.replace(tzinfo=timezone.utc)
        if proposal.expires_at.tzinfo is None
        else proposal.expires_at
    )
    if proposal.status == "pending" and datetime.now(timezone.utc) > expires_at:
        proposal.status = "expired"
        db.commit()
        db.refresh(proposal)

    return proposal


def confirm_proposal(
    db: Session,
    proposal_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> APIActionProposal:
    """
    CONFIRMATION state update.
    Marks proposal status as 'confirmed'.
    """
    proposal = get_proposal_by_id(db, proposal_id=proposal_id, owner_id=owner_id)

    if proposal.status == "expired":
        raise VerificationException(message="Action proposal has expired", status_code=400)
    if proposal.status == "rejected":
        raise VerificationException(message="Action proposal was previously rejected", status_code=400)
    if proposal.status in ("confirmed", "executed"):
        raise VerificationException(message="Action proposal has already been confirmed/executed", status_code=400)

    proposal.status = "confirmed"
    db.commit()
    db.refresh(proposal)
    return proposal


def reject_proposal(
    db: Session,
    proposal_id: uuid.UUID,
    owner_id: uuid.UUID,
    reason: Optional[str] = None,
) -> APIActionProposal:
    """
    REJECTION / CANCELLATION.
    Marks proposal status as 'rejected'.
    """
    proposal = get_proposal_by_id(db, proposal_id=proposal_id, owner_id=owner_id)

    if proposal.status == "executed":
        raise VerificationException(message="Cannot reject an already executed proposal", status_code=400)

    proposal.status = "rejected"
    db.commit()
    db.refresh(proposal)
    return proposal


def execute_confirmed_proposal(
    db: Session,
    proposal_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> ActionProposalResponse:
    """
    EXECUTE & AUDIT TRAIL:
    Strictly verifies proposal status is 'confirmed'.
    Executes request via execution service and attaches execution_result to proposal record.
    """
    proposal = get_proposal_by_id(db, proposal_id=proposal_id, owner_id=owner_id)

    if proposal.status == "pending":
        raise VerificationException(
            message="Unconfirmed action proposal cannot be executed. User confirmation required.",
            status_code=400,
        )
    if proposal.status == "expired":
        raise VerificationException(message="Cannot execute an expired action proposal", status_code=400)
    if proposal.status == "rejected":
        raise VerificationException(message="Cannot execute a rejected action proposal", status_code=400)
    if proposal.status == "executed":
        raise VerificationException(message="Action proposal has already been executed", status_code=400)

    # Execute request
    exec_req = ExecutionExecuteRequest(
        endpoint_id=proposal.endpoint_id,
        path_params=proposal.path_params,
        query_params=proposal.query_params,
        headers=proposal.headers,
        body=proposal.body,
        confirmed=True,
    )

    exec_result = execute_api_call(db=db, owner_id=owner_id, req=exec_req)

    proposal.status = "executed"
    proposal.execution_result = exec_result.model_dump(mode="json")
    db.commit()
    db.refresh(proposal)

    return _map_proposal_to_response(proposal)


def list_user_proposals(
    db: Session,
    owner_id: uuid.UUID,
    limit: int = 50,
) -> List[APIActionProposal]:
    """Lists user action proposals."""
    return list(
        db.execute(
            select(APIActionProposal)
            .where(APIActionProposal.user_id == owner_id)
            .order_by(APIActionProposal.created_at.desc())
            .limit(limit)
        ).scalars().all()
    )


def _map_proposal_to_response(p: APIActionProposal) -> ActionProposalResponse:
    return ActionProposalResponse(
        proposal_id=p.id,
        user_id=p.user_id,
        connection_id=p.connection_id,
        endpoint_id=p.endpoint_id,
        intent_summary=p.intent_summary,
        http_method=p.http_method,
        target_url=p.target_url,
        path_params=p.path_params,
        query_params=p.query_params,
        headers=p.headers,
        body=p.body,
        status=p.status,
        expires_at=p.expires_at,
        execution_result=p.execution_result,
        created_at=p.created_at,
    )
