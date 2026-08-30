import React, { useEffect, useState } from 'react';
import { catalogApi } from '../../api/catalog';
import { executionApi } from '../../api/execution';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { APIConnection, APIEndpoint, ExecutionPreviewResponse, ExecutionResponse } from '../../types/api';
import { Terminal, Play, Eye, AlertCircle, CheckCircle2, Layers } from 'lucide-react';

export const ExecutionPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState<string>('');

  const [pathParams, setPathParams] = useState('{}');
  const [queryParams, setQueryParams] = useState('{}');
  const [body, setBody] = useState('{}');
  const [confirmed, setConfirmed] = useState(false);

  const [previewData, setPreviewData] = useState<ExecutionPreviewResponse | null>(null);
  const [execResult, setExecResult] = useState<ExecutionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedApplicationId) {
      setConnections([]);
      setSelectedConnectionId('');
      return;
    }
    catalogApi.listConnections(selectedApplicationId).then((conns) => {
      setConnections(conns);
      if (conns.length > 0) {
        setSelectedConnectionId(conns[0].id);
      } else {
        setSelectedConnectionId('');
      }
    }).catch(() => []);
  }, [selectedApplicationId]);

  useEffect(() => {
    if (!selectedConnectionId) {
      setEndpoints([]);
      setSelectedEndpointId('');
      return;
    }

    catalogApi.getConnectionEndpoints(selectedConnectionId).then((eps) => {
      setEndpoints(eps);
      if (eps.length > 0) {
        setSelectedEndpointId(eps[0].id);
      } else {
        setSelectedEndpointId('');
      }
    }).catch(() => []);
  }, [selectedConnectionId]);

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="Direct API Execution Engine" />;
  }

  const handlePreview = async () => {
    if (!selectedEndpointId) {
      setError('Please select an endpoint from your API Catalog.');
      return;
    }

    setError(null);
    setExecResult(null);
    setLoading(true);

    try {
      const pParams = JSON.parse(pathParams || '{}');
      const qParams = JSON.parse(queryParams || '{}');
      const bPayload = JSON.parse(body || '{}');

      const res = await executionApi.preview({
        endpoint_id: selectedEndpointId,
        path_params: pParams,
        query_params: qParams,
        body: Object.keys(bPayload).length > 0 ? bPayload : undefined,
      });

      setPreviewData(res);
    } catch (err: any) {
      setError(err.message || 'Preview failed. Ensure JSON parameters format is valid.');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!selectedEndpointId) return;
    if (!confirmed) {
      setError('Explicit human confirmation checkbox must be checked prior to execution.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const pParams = JSON.parse(pathParams || '{}');
      const qParams = JSON.parse(queryParams || '{}');
      const bPayload = JSON.parse(body || '{}');

      const res = await executionApi.execute({
        endpoint_id: selectedEndpointId,
        path_params: pParams,
        query_params: qParams,
        body: Object.keys(bPayload).length > 0 ? bPayload : undefined,
        confirmed: true,
      });

      setExecResult(res);
    } catch (err: any) {
      setError(err.message || 'Execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Direct API Execution Engine</h1>
            {selectedApplication && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
                <Layers className="w-3 h-3 text-sky-600 mr-1" />
                {selectedApplication.name}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Dry-run preview and execute catalog API endpoints for application <span className="font-semibold text-slate-700">"{selectedApplication?.name}"</span> with required confirmation controls.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form Controls */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-sky-600" />
            <span>Execution Parameters</span>
          </h2>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2 animate-in fade-in duration-200">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Connection Picker */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Select API Connection</label>
            <select
              value={selectedConnectionId}
              onChange={(e) => setSelectedConnectionId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs"
            >
              {connections.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.base_url})</option>
              ))}
            </select>
          </div>

          {/* Endpoint Picker */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Select Catalog Endpoint</label>
            <select
              value={selectedEndpointId}
              onChange={(e) => setSelectedEndpointId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono"
            >
              {endpoints.map((ep) => (
                <option key={ep.id} value={ep.id}>
                  [{ep.method}] {ep.path} {ep.operation_id ? `(${ep.operation_id})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Path Parameters (JSON)</label>
            <textarea
              rows={2}
              value={pathParams}
              onChange={(e) => setPathParams(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Query Parameters (JSON)</label>
            <textarea
              rows={2}
              value={queryParams}
              onChange={(e) => setQueryParams(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Body Payload (JSON)</label>
            <textarea
              rows={3}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono resize-none"
            />
          </div>

          <div className="flex items-center space-x-2 pt-2">
            <input
              type="checkbox"
              id="confirm-check"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="w-4 h-4 text-sky-600 rounded border-slate-300 focus:ring-sky-500"
            />
            <label htmlFor="confirm-check" className="text-xs text-slate-700 font-semibold cursor-pointer">
              Explicit Human Confirmation Required for Execution
            </label>
          </div>

          <div className="flex space-x-3 pt-2">
            <button
              onClick={handlePreview}
              disabled={loading}
              className="flex-1 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>

            <button
              onClick={handleExecute}
              disabled={loading || !confirmed}
              className="flex-1 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Execute</span>
            </button>
          </div>
        </div>

        {/* Output & Preview Panel */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Request Inspection & Response</h2>

          {previewData && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs font-mono">
              <p className="font-bold text-slate-900 border-b border-slate-200 pb-1">Preview Inspection:</p>
              <p><span className="text-slate-500">Connection:</span> {previewData.connection_name}</p>
              <p><span className="text-slate-500">Target URL:</span> <span className="text-sky-700 font-bold">{previewData.target_url}</span></p>
              <p><span className="text-slate-500">Masked Headers:</span> {JSON.stringify(previewData.masked_headers)}</p>
            </div>
          )}

          {execResult && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between border-b border-emerald-200 pb-1">
                <p className="font-bold text-emerald-900 flex items-center space-x-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Execution Result ({execResult.status_code})</span>
                </p>
                <span className="text-slate-500">{execResult.latency_ms} ms</span>
              </div>
              <pre className="p-3 bg-white rounded-lg border border-emerald-100 overflow-x-auto text-slate-800">
                {JSON.stringify(execResult.response_body, null, 2)}
              </pre>
            </div>
          )}

          {!previewData && !execResult && (
            <div className="text-center py-16 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-slate-400">
              <p className="text-xs">Preview or execution output will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
