import React, { useEffect, useState } from 'react';
import { catalogApi } from '../../api/catalog';
import { openApiApi } from '../../api/openapi';
import { verificationApi } from '../../api/verification';
import { executionApi } from '../../api/execution';
import type { APIConnection, APISpecification, ActionProposalResponse, ExecutionResponse } from '../../types/api';
import { Database, Globe, ShieldCheck, History, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [specifications, setSpecifications] = useState<APISpecification[]>([]);
  const [proposals, setProposals] = useState<ActionProposalResponse[]>([]);
  const [executionLogs, setExecutionLogs] = useState<ExecutionResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [conns, specs, props, logs] = await Promise.all([
          catalogApi.listConnections().catch(() => []),
          openApiApi.listSpecifications().catch(() => []),
          verificationApi.listProposals().catch(() => []),
          executionApi.getLogs().catch(() => []),
        ]);
        setConnections(conns);
        setSpecifications(specs);
        setProposals(props);
        setExecutionLogs(logs);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const pendingProposals = proposals.filter((p) => p.status === 'pending');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Overview</h1>
        <p className="text-sm text-slate-500 mt-1">
          Monitor connected OpenAPI specs, catalog endpoints, RAG state, and execution proposals.
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Discovered Specs</p>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{loading ? '...' : specifications.length}</p>
          </div>
          <div className="p-3 bg-sky-50 text-sky-600 rounded-lg">
            <Globe className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">API Connections</p>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{loading ? '...' : connections.length}</p>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Database className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pending Approvals</p>
            <p className="text-2xl font-extrabold text-amber-600 mt-1">{loading ? '...' : pendingProposals.length}</p>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Executions</p>
            <p className="text-2xl font-extrabold text-emerald-600 mt-1">{loading ? '...' : executionLogs.length}</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <History className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Quick Access & Status Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Connections */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">Active API Connections</h2>
            <Link to="/api-catalog" className="text-sm text-sky-600 hover:text-sky-700 font-medium flex items-center">
              View All <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          {connections.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-lg">
              <Database className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-600">No active API connections</p>
              <p className="text-xs text-slate-400 mt-1">Discover an OpenAPI specification to get started</p>
              <Link
                to="/api-discovery"
                className="inline-flex items-center px-3 py-1.5 mt-3 text-xs font-medium text-white bg-sky-600 rounded-lg hover:bg-sky-500"
              >
                Discover Specs
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {connections.slice(0, 5).map((conn) => (
                <div key={conn.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{conn.name}</p>
                    <p className="text-xs text-slate-500 font-mono truncate max-w-xs">{conn.base_url}</p>
                  </div>
                  <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-full">
                    Active
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pending Verification Proposals */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">Pending Verification Proposals</h2>
            <Link to="/verification" className="text-sm text-sky-600 hover:text-sky-700 font-medium flex items-center">
              Review Proposals <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          {pendingProposals.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-lg">
              <ShieldCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-600">No pending verification proposals</p>
              <p className="text-xs text-slate-400 mt-1">Actions requiring human confirmation will appear here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingProposals.slice(0, 5).map((prop) => (
                <div key={prop.proposal_id} className="p-3 bg-amber-50/50 border border-amber-100 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 text-xs font-bold bg-amber-200 text-amber-900 rounded uppercase">
                        {prop.http_method}
                      </span>
                      <p className="text-sm font-semibold text-slate-900">{prop.intent_summary}</p>
                    </div>
                    <p className="text-xs text-slate-500 font-mono mt-1">{prop.target_url}</p>
                  </div>
                  <Link
                    to="/verification"
                    className="px-3 py-1 text-xs font-medium text-amber-900 bg-amber-200 rounded hover:bg-amber-300"
                  >
                    Review
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
