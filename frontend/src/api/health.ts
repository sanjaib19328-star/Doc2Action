const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://doc2action-api.onrender.com';

export interface HealthStatus {
  isOnline: boolean;
  status?: string;
  version?: string;
}

export const healthApi = {
  checkHealth: async (): Promise<HealthStatus> => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        return {
          isOnline: true,
          status: data.status || 'healthy',
          version: data.version,
        };
      }
      return { isOnline: false };
    } catch {
      return { isOnline: false };
    }
  },
};
