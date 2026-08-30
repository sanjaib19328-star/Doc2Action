import { apiRequest } from './client';
import type {
  DiscoverSpecRequest,
  APISpecification,
  APISpecificationDetail,
} from '../types/api';

export const openApiApi = {
  discover: (data: DiscoverSpecRequest): Promise<APISpecificationDetail> => {
    return apiRequest<APISpecificationDetail>('/openapi/discover', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listSpecifications: (applicationId?: string | null): Promise<APISpecification[]> => {
    const query = applicationId ? `?application_id=${encodeURIComponent(applicationId)}` : '';
    return apiRequest<APISpecification[]>(`/openapi/specifications${query}`, {
      method: 'GET',
    });
  },

  getSpecification: (specId: string): Promise<APISpecificationDetail> => {
    return apiRequest<APISpecificationDetail>(`/openapi/specifications/${specId}`, {
      method: 'GET',
    });
  },
};
