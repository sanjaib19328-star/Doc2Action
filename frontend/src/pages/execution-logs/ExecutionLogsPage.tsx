import React, { useEffect, useState, useCallback } from 'react';
import { executionApi } from '../../api/execution';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { ExecutionResponse } from '../../types/api';
import { History, Shield, AlertCircle, RefreshCw, Layers, Loader2 } from 'lucide-react';

export const ExecutionLogsPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [logs, setLogs] = useState<ExecutionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    if (!selectedApplicationId) {
      setLogs([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await executionApi.getLogs(selectedApplicationId);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load execution logs.');
    } finally {
      setLoading(false);
    }
  }, [selectedApplicationId]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="Execution Audit Logs" />;
  }

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Execution Audit Logs</h1>
            {selectedApplication && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
                <Layers className="w-3 h-3 text-sky-600 mr-1" />
                {selectedApplication.name}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Historical audit trail of all executed API operations for application <span className="font-semibold text-slate-700">"{selectedApplication?.name}"</span> with masked authorization headers and latency metrics.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-center space-x-2 animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <History className="w-4 h-4 text-emerald-600" />
            <span>Audit Logs ({logs.length})</span>
          </h2>
          <button
            onClick={fetchLogs}
            title="Refresh logs"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="text-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400 mx-auto" />
            <p className="text-xs text-slate-400 mt-2">Loading audit logs...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-slate-400">
            <p className="text-xs font-semibold text-slate-600">No execution logs found for this application</p>
          </div>
        ) : (
          <div className="space-y-3">
            {logs.map((log) => (
              <div key={log.execution_id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2 font-mono">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-2 gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.5 rounded font-bold uppercase bg-slate-200 text-slate-900 text-[10px]">
                      {log.method}
                    </span>
                    <span className="font-bold text-slate-900 truncate max-w-md">{log.target_url}</span>
                  </div>
                  <div className="flex items-center space-x-2 font-sans">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900">
                      HTTP {log.status_code || 200}
                    </span>
                    <span className="text-slate-500 font-semibold text-[11px]">{log.latency_ms} ms</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 text-slate-500 text-[11px]">
                  <Shield className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <span className="truncate">Masked Headers: {JSON.stringify(log.request_headers)}</span>
                </div>

                {log.response_body && (
                  <pre className="p-2.5 bg-white rounded-lg border border-slate-200 text-slate-800 overflow-x-auto max-h-32">
                    {JSON.stringify(log.response_body, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
