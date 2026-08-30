from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.agent.schemas import AgentProcessRequest, AgentStepResponse
from app.modules.agent.service import process_agent_intent

router = APIRouter()


@router.post(
    "/process",
    response_model=AgentStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Natural Language Query via AI Agent",
    description="Processes user intent, performs RAG catalog search, extracts parameters, and generates Human-in-the-Loop Action Proposal.",
)
def process_agent_query(
    req: AgentProcessRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgentStepResponse:
    """Processes user query and returns structured agent decision."""
    return process_agent_intent(db=db, owner_id=current_user.id, req=req)
