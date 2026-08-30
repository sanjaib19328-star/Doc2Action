from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentProcessRequest(BaseModel):
    query: str = Field(..., description="Natural language intent/command from the user")
    application_id: Optional[str] = Field(None, description="Optional application ID context for RAG search and proposal")
    connection_id: Optional[str] = Field(None, description="Optional connection ID filter for RAG search")
    conversation_state: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Current agent state")


class AgentStepResponse(BaseModel):
    step: str = Field(..., description="Current step in agent state machine (e.g. PLANNING, RAG_SEARCH, ENDPOINT_SELECTED, WAITING_FOR_INPUT, PROPOSED, COMPLETED, FAILED)")
    decision_type: str = Field(..., description="Classification of decision (e.g. INFORMATION, SEARCH_API, REQUEST_PARAMETERS, CREATE_PROPOSAL, WAIT_FOR_CONFIRMATION, EXECUTE, RESULT, ERROR)")
    text_message: str = Field(..., description="Agent message formatted for user")
    intent: Optional[str] = Field(None, description="Extracted user intent")
    selected_endpoint: Optional[Dict[str, Any]] = Field(None, description="Identified real catalog endpoint")
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters extracted so far")
    missing_parameters: List[str] = Field(default_factory=list, description="Missing required parameters")
    rag_hits: List[Dict[str, Any]] = Field(default_factory=list, description="RAG search candidate hits")
    proposal: Optional[Dict[str, Any]] = Field(None, description="Created action proposal detail if proposed")
    llm_configured: bool = Field(..., description="Whether Gemini LLM API key is present")
