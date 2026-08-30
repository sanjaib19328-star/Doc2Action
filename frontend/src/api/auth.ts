import { apiRequest } from './client';
import type { User, AuthToken, UserRegisterRequest, UserLoginRequest } from '../types/api';

export const authApi = {
  register: (data: UserRegisterRequest): Promise<User> => {
    return apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  login: (data: UserLoginRequest): Promise<AuthToken> => {
    return apiRequest<AuthToken>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getMe: (): Promise<User> => {
    return apiRequest<User>('/auth/me', {
      method: 'GET',
    });
  },
};
