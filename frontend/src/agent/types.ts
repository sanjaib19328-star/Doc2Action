import type {
  RAGSearchResult,
  APIEndpoint,
  APIConnection,
  ActionProposalResponse,
  ExecutionResponse,
} from '../types/api';

export type AgentStep =
  | 'IDLE'
  | 'THINKING'
  | 'SEARCHING'
  | 'PLANNING'
  | 'WAITING_FOR_INPUT'
  | 'PROPOSED'
  | 'WAITING_FOR_CONFIRMATION'
  | 'CONFIRMED'
  | 'EXECUTING'
  | 'COMPLETED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'FAILED';

export type AgentDecisionType =
  | 'INFORMATION'
  | 'SEARCH_API'
  | 'REQUEST_PARAMETERS'
  | 'CREATE_PROPOSAL'
  | 'WAIT_FOR_CONFIRMATION'
  | 'EXECUTE'
  | 'RESULT'
  | 'ERROR';

export interface StructuredAgentDecision {
  type: AgentDecisionType;
  explanation: string;
  intent_summary?: string;
  extracted_params?: {
    path_params?: Record<string, any>;
    query_params?: Record<string, any>;
    body?: Record<string, any>;
  };
  missing_params?: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  text: string;
  timestamp: string;
  step?: AgentStep;
  searchResults?: RAGSearchResult[];
  selectedEndpoint?: APIEndpoint;
  selectedConnection?: APIConnection;
  proposal?: ActionProposalResponse;
  executionResult?: ExecutionResponse;
  requiredParameters?: string[];
  decisionType?: AgentDecisionType;
}

export interface AgentConversationState {
  step: AgentStep;
  intent: string;
  selectedConnection: APIConnection | null;
  selectedEndpoint: APIEndpoint | null;
  extractedParameters: {
    path_params: Record<string, any>;
    query_params: Record<string, any>;
    body: Record<string, any>;
  };
  missingParameters: string[];
  activeProposal: ActionProposalResponse | null;
  executionResult: ExecutionResponse | null;
  error: string | null;
  llmConfigured: boolean;
}
