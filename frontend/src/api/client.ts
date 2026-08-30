const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

class APIClientError extends Error {
  status: number;
  details?: any;

  constructor(message: string, status: number, details?: any) {
    super(message);
    this.name = 'APIClientError';
    this.status = status;
    this.details = details;
  }
}

export const getStoredToken = (): string | null => {
  return localStorage.getItem('doc2action_access_token');
};

export const setStoredToken = (token: string): void => {
  localStorage.setItem('doc2action_access_token', token);
};

export const removeStoredToken = (): void => {
  localStorage.removeItem('doc2action_access_token');
};

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;
  const token = getStoredToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      // Handle 401 Unauthorized globally
      if (response.status === 401) {
        removeStoredToken();
      }

      let errorMessage = 'An error occurred during request execution';
      let errorDetails = null;

      if (data) {
        if (data.error && data.error.message) {
          errorMessage = data.error.message;
          errorDetails = data.error.details;
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        }
      }

      throw new APIClientError(errorMessage, response.status, errorDetails);
    }

    return data as T;
  } catch (err) {
    if (err instanceof APIClientError) {
      throw err;
    }
    throw new APIClientError(
      err instanceof Error ? err.message : 'Network failure or server unreachable',
      0
    );
  }
}

export { APIClientError };
