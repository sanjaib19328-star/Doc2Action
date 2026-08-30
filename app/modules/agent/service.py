import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import BaseAppException
from app.core.config import settings
from app.modules.catalog.models import APIEndpoint, APIConnection
from app.modules.catalog.service import get_connection_endpoints, get_connection_by_id
from app.modules.rag.service import semantic_search_catalog
from app.modules.verification.schemas import CreateActionProposalRequest
from app.modules.verification.service import create_proposal, _map_proposal_to_response
from app.modules.agent.schemas import AgentProcessRequest, AgentStepResponse

logger = logging.getLogger("doc2action")


class AgentException(BaseAppException):
    def __init__(self, message: str = "Agent execution failed", status_code: int = 400) -> None:
        super().__init__(message=message, status_code=status_code)


def is_gemini_configured() -> bool:
    api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return bool(api_key and api_key.strip())


def process_agent_intent(
    db: Session,
    owner_id: Any,
    req: AgentProcessRequest,
) -> AgentStepResponse:
    query = req.query.strip()
    if not query:
        raise AgentException(message="User query cannot be empty", status_code=400)

    llm_active = is_gemini_configured()

    # 1. RAG Search over real user catalog
    app_uuid = None
    if req.application_id:
        try:
            import uuid
            app_uuid = uuid.UUID(req.application_id)
        except ValueError:
            pass

    connection_uuid = None
    if req.connection_id:
        try:
            import uuid
            connection_uuid = uuid.UUID(req.connection_id)
        except ValueError:
            pass

    rag_results = semantic_search_catalog(
        owner_id=owner_id,
        query=query,
        application_id=app_uuid,
        connection_id=connection_uuid,
        top_k=5,
    )

    if not rag_results:
        return AgentStepResponse(
            step="FAILED",
            decision_type="ERROR",
            text_message="No matching API endpoints found in your registered API Catalog RAG index. Please ensure you have connected an OpenAPI specification and indexed it on the API Catalog page.",
            intent=query,
            rag_hits=[],
            llm_configured=llm_active,
        )

    # 2. Select best real catalog endpoint from RAG hits
    top_hit = rag_results[0]
    endpoint_id_str = top_hit.get("endpoint_id")

    if not endpoint_id_str:
        return AgentStepResponse(
            step="FAILED",
            decision_type="ERROR",
            text_message="RAG search returned a result without a valid endpoint reference.",
            intent=query,
            rag_hits=rag_results,
            llm_configured=llm_active,
        )

    import uuid
    endpoint_uuid = uuid.UUID(endpoint_id_str)
    
    # Query database for actual endpoint record
    endpoint = db.query(APIEndpoint).filter(APIEndpoint.id == endpoint_uuid).first()
    if not endpoint:
        return AgentStepResponse(
            step="FAILED",
            decision_type="ERROR",
            text_message=f"Endpoint ID {endpoint_id_str} referenced in RAG not found in catalog database.",
            intent=query,
            rag_hits=rag_results,
            llm_configured=llm_active,
        )

    connection = db.query(APIConnection).filter(APIConnection.id == endpoint.connection_id, APIConnection.owner_id == owner_id).first()
    if not connection:
        return AgentStepResponse(
            step="FAILED",
            decision_type="ERROR",
            text_message="Access denied or API connection not owned by user.",
            intent=query,
            rag_hits=rag_results,
            llm_configured=llm_active,
        )

    # 3. Analyze Endpoint Parameters & Extract from Query
    parameters_def = endpoint.parameters or []
    req_body_schema = endpoint.request_body_schema or {}

    extracted_params: Dict[str, Any] = {
        "path_params": {},
        "query_params": {},
        "body": None,
    }
    missing_required_params: List[str] = []

    query_lower = query.lower()

    for p in parameters_def:
        p_name = p.get("name")
        p_in = p.get("in", "query")
        p_required = p.get("required", False)

        val = None
        if p_name and p_name.lower() in query_lower:
            words = query.split()
            for idx, w in enumerate(words):
                if p_name.lower() in w.lower():
                    if "=" in w:
                        val = w.split("=")[-1]
                    elif idx + 1 < len(words) and words[idx + 1].lower() in ("available", "pending", "sold"):
                        val = words[idx + 1]
                    break

        if not val:
            if p_name == "status":
                if "available" in query_lower:
                    val = "available"
                elif "pending" in query_lower:
                    val = "pending"
                elif "sold" in query_lower:
                    val = "sold"

        if val:
            if p_in == "path":
                extracted_params["path_params"][p_name] = val
            else:
                extracted_params["query_params"][p_name] = val
        elif p_required:
            missing_required_params.append(p_name)

    # If parameters missing, prompt user
    if missing_required_params:
        return AgentStepResponse(
            step="WAITING_FOR_INPUT",
            decision_type="REQUEST_PARAMETERS",
            text_message=f"I identified the endpoint [{endpoint.method.upper()}] {endpoint.path} from your catalog, but required parameters are missing: {', '.join(missing_required_params)}. Please supply them.",
            intent=query,
            selected_endpoint={
                "id": str(endpoint.id),
                "connection_id": str(connection.id),
                "method": endpoint.method.upper(),
                "path": endpoint.path,
                "summary": endpoint.summary,
            },
            extracted_parameters=extracted_params,
            missing_parameters=missing_required_params,
            rag_hits=rag_results,
            llm_configured=llm_active,
        )

    # 4. Generate Action Proposal using verification service
    effective_app_id = app_uuid or connection.application_id
    proposal_req = CreateActionProposalRequest(
        endpoint_id=str(endpoint.id),
        application_id=effective_app_id,
        intent_summary=f"[AI Agent] {query}",
        path_params=extracted_params["path_params"],
        query_params=extracted_params["query_params"],
        body=extracted_params["body"],
        ttl_seconds=300,
    )

    proposal = create_proposal(db=db, owner_id=owner_id, req=proposal_req)
    proposal_resp = _map_proposal_to_response(proposal)

    return AgentStepResponse(
        step="WAITING_FOR_CONFIRMATION",
        decision_type="WAIT_FOR_CONFIRMATION",
        text_message=f"I selected [{endpoint.method.upper()}] {endpoint.path} from your API Catalog and generated a Human-in-the-Loop Action Proposal (ID: {proposal.id}). Confirmation required before execution.",
        intent=query,
        selected_endpoint={
            "id": str(endpoint.id),
            "connection_id": str(connection.id),
            "method": endpoint.method.upper(),
            "path": endpoint.path,
            "summary": endpoint.summary,
        },
        extracted_parameters=extracted_params,
        missing_parameters=[],
        rag_hits=rag_results,
        proposal=proposal_resp.model_dump(mode="json"),
        llm_configured=llm_active,
    )
