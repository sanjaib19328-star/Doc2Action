import React, { useEffect, useState } from 'react';
import { catalogApi } from '../../api/catalog';
import { openApiApi } from '../../api/openapi';
import { verificationApi } from '../../api/verification';
import { executionApi } from '../../api/execution';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { APIConnection, APISpecification, ActionProposalResponse, ExecutionResponse } from '../../types/api';
import { Database, Globe, ShieldCheck, History, ArrowRight, Layers, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [specifications, setSpecifications] = useState<APISpecification[]>([]);
  const [proposals, setProposals] = useState<ActionProposalResponse[]>([]);
  const [executionLogs, setExecutionLogs] = useState<ExecutionResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedApplicationId) {
      setConnections([]);
      setSpecifications([]);
      setProposals([]);
      setExecutionLogs([]);
      setLoading(false);
      return;
    }

    let isMounted = true;
    setLoading(true);

    const fetchDashboardData = async () => {
      try {
        const [conns, specs, props, logs] = await Promise.all([
          catalogApi.listConnections(selectedApplicationId).catch(() => []),
          openApiApi.listSpecifications(selectedApplicationId).catch(() => []),
          verificationApi.listProposals(selectedApplicationId).catch(() => []),
          executionApi.getLogs(selectedApplicationId).catch(() => []),
        ]);
        if (isMounted) {
          setConnections(conns);
          setSpecifications(specs);
          setProposals(props);
          setExecutionLogs(logs);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDashboardData();

    return () => {
      isMounted = false;
    };
  }, [selectedApplicationId]);

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="the application dashboard" />;
  }

  const pendingProposals = proposals.filter((p) => p.status === 'pending');

  return (
    <div className="space-y-6 font-sans">
      {/* Application Context Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
              <Layers className="w-3 h-3 text-sky-600 mr-1" />
              Active Workspace
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              ID: {selectedApplication?.id}
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight mt-1">
            {selectedApplication?.name || 'Application Overview'}
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            {selectedApplication?.description || 'No description configured for this application. Manage isolated OpenAPI specs, catalog connections, and AI actions.'}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Link
            to="/api-discovery"
            className="inline-flex items-center justify-center px-3.5 py-2 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 rounded-xl shadow-xs transition-colors space-x-1.5"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Discover API</span>
          </Link>
          <Link
            to="/applications"
            className="inline-flex items-center justify-center px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors space-x-1.5"
          >
            <span>Switch App</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Discovered Specs</p>
            <p className="text-2xl font-black text-slate-900 mt-1">{loading ? '...' : specifications.length}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Isolated to this app</p>
          </div>
          <div className="p-3 bg-sky-50 text-sky-600 rounded-xl border border-sky-100">
            <Globe className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">API Connections</p>
            <p className="text-2xl font-black text-slate-900 mt-1">{loading ? '...' : connections.length}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Catalog endpoints</p>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl border border-indigo-100">
            <Database className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Pending Approvals</p>
            <p className="text-2xl font-black text-amber-600 mt-1">{loading ? '...' : pendingProposals.length}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Human verification</p>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl border border-amber-100">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Executions</p>
            <p className="text-2xl font-black text-emerald-600 mt-1">{loading ? '...' : executionLogs.length}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Audit log records</p>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
            <History className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Quick Access & Status Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Connections */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Database className="w-4 h-4 text-sky-600" />
              <span>Active API Connections ({connections.length})</span>
            </h2>
            <Link to="/api-catalog" className="text-xs text-sky-600 hover:text-sky-700 font-semibold flex items-center">
              View All <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>

          {connections.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
              <Database className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-700">No active API connections in this application</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Discover an OpenAPI specification to get started</p>
              <Link
                to="/api-discovery"
                className="inline-flex items-center px-3 py-1.5 mt-3 text-xs font-semibold text-white bg-sky-600 rounded-lg hover:bg-sky-500"
              >
                Discover Specs
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5">
              {connections.slice(0, 5).map((conn) => (
                <div key={conn.id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-slate-900">{conn.name}</p>
                    <p className="text-[10px] text-slate-500 font-mono truncate max-w-xs">{conn.base_url}</p>
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-100 text-emerald-800 rounded-full">
                    Active
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pending Verification Proposals */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-amber-600" />
              <span>Pending Action Proposals ({pendingProposals.length})</span>
            </h2>
            <Link to="/verification" className="text-xs text-sky-600 hover:text-sky-700 font-semibold flex items-center">
              Review <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>

          {pendingProposals.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
              <ShieldCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-700">No pending verification proposals</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Actions requiring human confirmation will appear here</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {pendingProposals.slice(0, 5).map((prop) => (
                <div key={prop.proposal_id} className="p-3 bg-amber-50/50 border border-amber-100 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="px-1.5 py-0.5 text-[10px] font-bold bg-amber-200 text-amber-900 rounded uppercase">
                        {prop.http_method}
                      </span>
                      <p className="text-xs font-bold text-slate-900 truncate max-w-xs">{prop.intent_summary}</p>
                    </div>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">{prop.target_url}</p>
                  </div>
                  <Link
                    to="/verification"
                    className="px-2.5 py-1 text-xs font-semibold text-amber-900 bg-amber-200 rounded-lg hover:bg-amber-300"
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
