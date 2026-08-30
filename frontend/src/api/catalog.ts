import { apiRequest } from './client';
import type {
  APIConnectionCreate,
  APIConnection,
  APIConnectionDetail,
  APIEndpoint,
} from '../types/api';

export const catalogApi = {
  createConnection: (data: APIConnectionCreate): Promise<APIConnectionDetail> => {
    return apiRequest<APIConnectionDetail>('/catalog/connections', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listConnections: (applicationId?: string | null): Promise<APIConnection[]> => {
    const query = applicationId ? `?application_id=${encodeURIComponent(applicationId)}` : '';
    return apiRequest<APIConnection[]>(`/catalog/connections${query}`, {
      method: 'GET',
    });
  },

  getConnection: (connectionId: string): Promise<APIConnectionDetail> => {
    return apiRequest<APIConnectionDetail>(`/catalog/connections/${connectionId}`, {
      method: 'GET',
    });
  },

  getConnectionEndpoints: (connectionId: string): Promise<APIEndpoint[]> => {
    return apiRequest<APIEndpoint[]>(`/catalog/connections/${connectionId}/endpoints`, {
      method: 'GET',
    });
  },

  deleteConnection: (connectionId: string): Promise<{ message: string; id: string }> => {
    return apiRequest<{ message: string; id: string }>(`/catalog/connections/${connectionId}`, {
      method: 'DELETE',
    });
  },
};
