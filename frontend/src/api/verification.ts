import { apiRequest } from './client';
import type {
  CreateActionProposalRequest,
  ActionProposalResponse,
  RejectProposalRequest,
} from '../types/api';

export const verificationApi = {
  propose: (data: CreateActionProposalRequest): Promise<ActionProposalResponse> => {
    return apiRequest<ActionProposalResponse>('/verification/propose', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listProposals: (applicationId?: string | null, limit = 50): Promise<ActionProposalResponse[]> => {
    let url = `/verification/proposals?limit=${limit}`;
    if (applicationId) {
      url += `&application_id=${encodeURIComponent(applicationId)}`;
    }
    return apiRequest<ActionProposalResponse[]>(url, {
      method: 'GET',
    });
  },

  getProposal: (proposalId: string): Promise<ActionProposalResponse> => {
    return apiRequest<ActionProposalResponse>(`/verification/proposals/${proposalId}`, {
      method: 'GET',
    });
  },

  confirmProposal: (proposalId: string): Promise<ActionProposalResponse> => {
    return apiRequest<ActionProposalResponse>(`/verification/proposals/${proposalId}/confirm`, {
      method: 'POST',
    });
  },

  rejectProposal: (
    proposalId: string,
    data?: RejectProposalRequest
  ): Promise<ActionProposalResponse> => {
    return apiRequest<ActionProposalResponse>(`/verification/proposals/${proposalId}/reject`, {
      method: 'POST',
      body: JSON.stringify(data || { reason: 'User rejected proposal' }),
    });
  },

  executeProposal: (proposalId: string): Promise<ActionProposalResponse> => {
    return apiRequest<ActionProposalResponse>(`/verification/proposals/${proposalId}/execute`, {
      method: 'POST',
    });
  },
};
