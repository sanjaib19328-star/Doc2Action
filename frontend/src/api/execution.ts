import { apiRequest } from './client';
import type {
  ExecutionPreviewRequest,
  ExecutionPreviewResponse,
  ExecutionExecuteRequest,
  ExecutionResponse,
} from '../types/api';

export const executionApi = {
  preview: (data: ExecutionPreviewRequest): Promise<ExecutionPreviewResponse> => {
    return apiRequest<ExecutionPreviewResponse>('/execution/preview', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  execute: (data: ExecutionExecuteRequest): Promise<ExecutionResponse> => {
    return apiRequest<ExecutionResponse>('/execution/execute', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getLogs: (applicationId?: string | null, limit = 50): Promise<ExecutionResponse[]> => {
    let url = `/execution/logs?limit=${limit}`;
    if (applicationId) {
      url += `&application_id=${encodeURIComponent(applicationId)}`;
    }
    return apiRequest<ExecutionResponse[]>(url, {
      method: 'GET',
    });
  },
};
