import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, UserLoginRequest, UserRegisterRequest } from '../types/api';
import { authApi } from '../api/auth';
import { getStoredToken, setStoredToken, removeStoredToken } from '../api/client';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (data: UserRegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await authApi.getMe();
      setUser(currentUser);
    } catch {
      removeStoredToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (credentials: UserLoginRequest) => {
    setIsLoading(true);
    try {
      const tokenResponse = await authApi.login(credentials);
      setStoredToken(tokenResponse.access_token);
      const currentUser = await authApi.getMe();
      setUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: UserRegisterRequest) => {
    setIsLoading(true);
    try {
      await authApi.register(data);
      // Auto login after successful registration
      const tokenResponse = await authApi.login({ email: data.email, password: data.password });
      setStoredToken(tokenResponse.access_token);
      const currentUser = await authApi.getMe();
      setUser(currentUser);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    removeStoredToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
