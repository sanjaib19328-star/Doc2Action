import React, { useEffect, useState } from 'react';
import { executionApi } from '../../api/execution';
import type { ExecutionResponse } from '../../types/api';
import { History, Shield, AlertCircle, RefreshCw } from 'lucide-react';

export const ExecutionLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<ExecutionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await executionApi.getLogs();
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load execution logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Execution Audit Logs</h1>
        <p className="text-sm text-slate-500 mt-1">
          Historical audit trail of all executed API operations with masked authorization headers and latency metrics.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <History className="w-5 h-5 text-emerald-600" />
            <span>Audit Logs ({logs.length})</span>
          </h2>
          <button
            onClick={fetchLogs}
            title="Refresh logs"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <p className="text-xs text-slate-400">Loading audit logs...</p>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-200 rounded-lg text-slate-400">
            <p className="text-sm font-medium">No execution logs found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {logs.map((log) => (
              <div key={log.execution_id} className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2 font-mono">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-2 gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded font-bold uppercase bg-slate-200 text-slate-900">
                      {log.method}
                    </span>
                    <span className="font-bold text-slate-900 truncate max-w-md">{log.target_url}</span>
                  </div>
                  <div className="flex items-center space-x-2 font-sans">
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-900">
                      HTTP {log.status_code || 200}
                    </span>
                    <span className="text-slate-500 font-semibold">{log.latency_ms} ms</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 text-slate-500">
                  <Shield className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Masked Headers: {JSON.stringify(log.request_headers)}</span>
                </div>

                {log.response_body && (
                  <pre className="p-2 bg-white rounded border border-slate-200 text-slate-800 overflow-x-auto max-h-32">
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
