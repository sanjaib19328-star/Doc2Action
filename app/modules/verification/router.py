import uuid
from typing import List
from fastapi import APIRouter, Depends, status
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
    summary="Propose an API Action",
    description="Validates target endpoint and parameters, builds preview target URL, and creates a pending action proposal.",
)
def propose_action(
    req: CreateActionProposalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.create_proposal(db=db, owner_id=current_user.id, req=req)
    return service._map_proposal_to_response(proposal)


@router.get(
    "/proposals",
    response_model=List[ActionProposalResponse],
    status_code=status.HTTP_200_OK,
    summary="List Action Proposals",
    description="Retrieves all action proposals for the authenticated user.",
)
def list_proposals(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[ActionProposalResponse]:
    proposals = service.list_user_proposals(db=db, owner_id=current_user.id, limit=limit)
    return [service._map_proposal_to_response(p) for p in proposals]


@router.get(
    "/proposals/{proposal_id}",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Action Proposal Details",
    description="Retrieves details and status of a specific action proposal.",
)
def get_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.get_proposal_by_id(db=db, proposal_id=proposal_id, owner_id=current_user.id)
    return service._map_proposal_to_response(proposal)


@router.post(
    "/proposals/{proposal_id}/confirm",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm Action Proposal",
    description="User confirms a pending action proposal.",
)
def confirm_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.confirm_proposal(db=db, proposal_id=proposal_id, owner_id=current_user.id)
    return service._map_proposal_to_response(proposal)


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject/Cancel Action Proposal",
    description="User rejects or cancels an action proposal.",
)
def reject_proposal(
    proposal_id: uuid.UUID,
    req: RejectProposalRequest = RejectProposalRequest(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    proposal = service.reject_proposal(
        db=db, proposal_id=proposal_id, owner_id=current_user.id, reason=req.reason
    )
    return service._map_proposal_to_response(proposal)


@router.post(
    "/proposals/{proposal_id}/execute",
    response_model=ActionProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Confirmed Action Proposal",
    description="Executes a confirmed action proposal and records execution result in audit trail.",
)
def execute_proposal(
    proposal_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ActionProposalResponse:
    return service.execute_confirmed_proposal(
        db=db, proposal_id=proposal_id, owner_id=current_user.id
    )
