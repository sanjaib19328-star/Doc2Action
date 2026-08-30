import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './routes/ProtectedRoute';

import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { ApiDiscoveryPage } from './pages/api-discovery/ApiDiscoveryPage';
import { ApiCatalogPage } from './pages/api-catalog/ApiCatalogPage';
import { ConnectionDetailPage } from './pages/api-catalog/ConnectionDetailPage';
import { RagPage } from './pages/rag/RagPage';
import { AgentPage } from './pages/workflows/AgentPage';
import { VerificationPage } from './pages/workflows/VerificationPage';
import { ExecutionPage } from './pages/execution/ExecutionPage';
import { ExecutionLogsPage } from './pages/execution-logs/ExecutionLogsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Application Shell Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/api-discovery" element={<ApiDiscoveryPage />} />
            <Route path="/api-catalog" element={<ApiCatalogPage />} />
            <Route path="/api-catalog/:connectionId" element={<ConnectionDetailPage />} />
            <Route path="/rag" element={<RagPage />} />
            <Route path="/agent" element={<AgentPage />} />
            <Route path="/verification" element={<VerificationPage />} />
            <Route path="/execution" element={<ExecutionPage />} />
            <Route path="/execution-logs" element={<ExecutionLogsPage />} />
          </Route>

          {/* Fallback wildcard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
