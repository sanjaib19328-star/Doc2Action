import { apiRequest } from './client';
import type {
  RAGSearchRequest,
  RAGSearchResult,
  RAGIndexResponse,
  RAGDeleteResponse,
} from '../types/api';

export const ragApi = {
  indexConnection: (connectionId: string): Promise<RAGIndexResponse> => {
    return apiRequest<RAGIndexResponse>(`/rag/index/${connectionId}`, {
      method: 'POST',
    });
  },

  reindexConnection: (connectionId: string): Promise<RAGIndexResponse> => {
    return apiRequest<RAGIndexResponse>(`/rag/reindex/${connectionId}`, {
      method: 'POST',
    });
  },

  deleteIndex: (connectionId: string): Promise<RAGDeleteResponse> => {
    return apiRequest<RAGDeleteResponse>(`/rag/index/${connectionId}`, {
      method: 'DELETE',
    });
  },

  search: (data: RAGSearchRequest): Promise<RAGSearchResult[]> => {
    return apiRequest<RAGSearchResult[]>('/rag/search', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
