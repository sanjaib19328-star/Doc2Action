import { apiRequest } from './client';
import type { Application, ApplicationCreate, ApplicationUpdate } from '../types/api';

export const applicationsApi = {
  list: (): Promise<Application[]> => {
    return apiRequest<Application[]>('/applications', {
      method: 'GET',
    });
  },

  get: (applicationId: string): Promise<Application> => {
    return apiRequest<Application>(`/applications/${applicationId}`, {
      method: 'GET',
    });
  },

  create: (data: ApplicationCreate): Promise<Application> => {
    return apiRequest<Application>('/applications', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (applicationId: string, data: ApplicationUpdate): Promise<Application> => {
    return apiRequest<Application>(`/applications/${applicationId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: (applicationId: string): Promise<void> => {
    return apiRequest<void>(`/applications/${applicationId}`, {
      method: 'DELETE',
    });
  },
};
