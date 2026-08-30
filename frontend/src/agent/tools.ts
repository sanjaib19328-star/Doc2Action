import { ragApi } from '../api/rag';
import { catalogApi } from '../api/catalog';
import { verificationApi } from '../api/verification';
import { executionApi } from '../api/execution';
import type {
  RAGSearchResult,
  APIConnection,
  APIEndpoint,
  ActionProposalResponse,
  CreateActionProposalRequest,
  ExecutionResponse,
} from '../types/api';

/**
 * Agent Tools mapping directly to backend API services.
 * Arbitrary execution is strictly prohibited.
 */
export const agentTools = {
  searchApiCatalog: async (query: string, applicationId?: string, connectionId?: string): Promise<RAGSearchResult[]> => {
    return ragApi.search({ query, application_id: applicationId, connection_id: connectionId, top_k: 5 });
  },

  listConnections: async (applicationId?: string): Promise<APIConnection[]> => {
    return catalogApi.listConnections(applicationId);
  },

  getConnectionEndpoints: async (connectionId: string): Promise<APIEndpoint[]> => {
    return catalogApi.getConnectionEndpoints(connectionId);
  },

  createActionProposal: async (request: CreateActionProposalRequest): Promise<ActionProposalResponse> => {
    return verificationApi.propose(request);
  },

  confirmActionProposal: async (proposalId: string): Promise<ActionProposalResponse> => {
    return verificationApi.confirmProposal(proposalId);
  },

  rejectActionProposal: async (proposalId: string, reason?: string): Promise<ActionProposalResponse> => {
    return verificationApi.rejectProposal(proposalId, { reason });
  },

  executeConfirmedAction: async (proposalId: string): Promise<ActionProposalResponse> => {
    return verificationApi.executeProposal(proposalId);
  },

  getExecutionLogs: async (applicationId?: string, limit = 20): Promise<ExecutionResponse[]> => {
    return executionApi.getLogs(applicationId, limit);
  },
};
