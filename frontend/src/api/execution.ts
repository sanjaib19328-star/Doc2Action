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

  getLogs: (limit = 50): Promise<ExecutionResponse[]> => {
    return apiRequest<ExecutionResponse[]>(`/execution/logs?limit=${limit}`, {
      method: 'GET',
    });
  },
};
