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

  listConnections: (): Promise<APIConnection[]> => {
    return apiRequest<APIConnection[]>('/catalog/connections', {
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
