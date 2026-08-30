import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Application, ApplicationCreate, ApplicationUpdate } from '../types/api';
import { applicationsApi } from '../api/applications';
import { useAuth } from './AuthContext';

interface ApplicationContextType {
  applications: Application[];
  selectedApplication: Application | null;
  selectedApplicationId: string | null;
  isLoading: boolean;
  error: string | null;
  selectApplication: (appId: string | null) => void;
  refreshApplications: () => Promise<Application[]>;
  createApplication: (data: ApplicationCreate) => Promise<Application>;
  updateApplication: (id: string, data: ApplicationUpdate) => Promise<Application>;
  deleteApplication: (id: string) => Promise<void>;
}

const ApplicationContext = createContext<ApplicationContextType | undefined>(undefined);

const STORAGE_KEY = 'doc2action_selected_application_id';

export const ApplicationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState<string | null>(() => {
    return localStorage.getItem(STORAGE_KEY);
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshApplications = useCallback(async (): Promise<Application[]> => {
    if (!isAuthenticated) {
      setApplications([]);
      setSelectedApplicationId(null);
      setIsLoading(false);
      return [];
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await applicationsApi.list();
      setApplications(data);

      setSelectedApplicationId((prevId) => {
        if (data.length === 0) {
          localStorage.removeItem(STORAGE_KEY);
          return null;
        }

        // If previously selected application still exists in list, keep it
        const exists = data.some((app) => app.id === prevId);
        if (prevId && exists) {
          return prevId;
        }

        // Otherwise default to first available application
        const firstId = data[0].id;
        localStorage.setItem(STORAGE_KEY, firstId);
        return firstId;
      });

      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to load applications');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshApplications();
  }, [refreshApplications]);

  const selectApplication = useCallback((appId: string | null) => {
    if (!appId) {
      localStorage.removeItem(STORAGE_KEY);
      setSelectedApplicationId(null);
      return;
    }
    localStorage.setItem(STORAGE_KEY, appId);
    setSelectedApplicationId(appId);
  }, []);

  const createApplication = async (data: ApplicationCreate): Promise<Application> => {
    setIsLoading(true);
    setError(null);
    try {
      const newApp = await applicationsApi.create(data);
      const updatedList = await applicationsApi.list();
      setApplications(updatedList);
      selectApplication(newApp.id);
      return newApp;
    } catch (err: any) {
      setError(err.message || 'Failed to create application');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateApplication = async (id: string, data: ApplicationUpdate): Promise<Application> => {
    setIsLoading(true);
    setError(null);
    try {
      const updated = await applicationsApi.update(id, data);
      const updatedList = await applicationsApi.list();
      setApplications(updatedList);
      return updated;
    } catch (err: any) {
      setError(err.message || 'Failed to update application');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteApplication = async (id: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    try {
      await applicationsApi.delete(id);
      const updatedList = await applicationsApi.list();
      setApplications(updatedList);

      if (selectedApplicationId === id) {
        if (updatedList.length > 0) {
          selectApplication(updatedList[0].id);
        } else {
          selectApplication(null);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete application');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const selectedApplication = applications.find((app) => app.id === selectedApplicationId) || null;

  return (
    <ApplicationContext.Provider
      value={{
        applications,
        selectedApplication,
        selectedApplicationId,
        isLoading,
        error,
        selectApplication,
        refreshApplications,
        createApplication,
        updateApplication,
        deleteApplication,
      }}
    >
      {children}
    </ApplicationContext.Provider>
  );
};

export const useApplication = (): ApplicationContextType => {
  const context = useContext(ApplicationContext);
  if (!context) {
    throw new Error('useApplication must be used within an ApplicationProvider');
  }
  return context;
};
