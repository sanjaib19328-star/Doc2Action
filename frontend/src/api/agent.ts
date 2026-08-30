import { apiRequest } from './client';
import type { ActionProposalResponse } from '../types/api';

export interface AgentProcessBackendRequest {
  query: string;
  application_id?: string | null;
  connection_id?: string;
  conversation_state?: Record<string, any>;
}

export interface AgentStepBackendResponse {
  step: string;
  decision_type: string;
  text_message: string;
  intent?: string;
  selected_endpoint?: {
    id: string;
    connection_id: string;
    method: string;
    path: string;
    summary?: string;
  };
  extracted_parameters: Record<string, any>;
  missing_parameters: string[];
  rag_hits: any[];
  proposal?: ActionProposalResponse;
  llm_configured: boolean;
}

export const agentApi = {
  processQuery: (data: AgentProcessBackendRequest): Promise<AgentStepBackendResponse> => {
    return apiRequest<AgentStepBackendResponse>('/agent/process', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
