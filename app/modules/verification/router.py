import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.verification.schemas import (
    CreateActionProposalRequest,
    ActionProposalResponse,
    RejectProposalRequest,
)
from app.modules.verification import service

router = APIRouter()


@router.post(
    "/propose",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Action Proposal (Human-in-the-Loop)",
    description="Validates target endpoint and parameters, masks headers, and constructs a pending proposal.",
)
def create_action_proposal(
    request: CreateActionProposalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.create_proposal(
        db=db, owner_id=current_user.id, req=request
    )
    return service._map_proposal_to_response(proposal)


@router.get(
    "/proposals",
    response_model=List[ActionProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="List Action Proposals",
    description="Retrieves action proposals for the user, optionally filtered by application_id.",
)
def list_proposals(
    application_id: Optional[uuid.UUID] = Query(None, description="Optional application ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ActionProposalResponse]:
    proposals = service.list_user_proposals(
        db=db, owner_id=current_user.id, application_id=application_id
    )
    return [service._map_proposal_to_response(p) for p in proposals]


@router.get(
    "/proposals/{proposal_id}",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Action Proposal Detail",
    description="Retrieves a single proposal enforcing user isolation.",
)
def get_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.get_proposal_by_id(
        db=db, proposal_id=proposal_id, owner_id=current_user.id
    )
    return service._map_proposal_to_response(proposal)


@router.post(
    "/proposals/{proposal_id}/confirm",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Human Confirmation of Action Proposal",
    description="Updates proposal status to confirmed.",
)
def confirm_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.confirm_proposal(
        db=db, proposal_id=proposal_id, owner_id=current_user.id
    )
    return service._map_proposal_to_response(proposal)


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Action Proposal",
    description="Rejects an action proposal.",
)
def reject_proposal(
    proposal_id: uuid.UUID,
    body: Optional[RejectProposalRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    reason = body.reason if body else "User rejected proposal"
    proposal = service.reject_proposal(
        db=db, proposal_id=proposal_id, owner_id=current_user.id, reason=reason
    )
    return service._map_proposal_to_response(proposal)


@router.post(
    "/proposals/{proposal_id}/execute",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Confirmed Action Proposal",
    description="Executes a confirmed proposal and records execution audit result.",
)
def execute_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    return service.execute_confirmed_proposal(
        db=db, proposal_id=proposal_id, owner_id=current_user.id
    )
