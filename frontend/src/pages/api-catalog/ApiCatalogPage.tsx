import React, { useEffect, useState } from 'react';
import { catalogApi } from '../../api/catalog';
import { ragApi } from '../../api/rag';
import type { APIConnection, APIEndpoint } from '../../types/api';
import { Database, Trash2, Layers, Cpu, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export const ApiCatalogPage: React.FC = () => {
  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [deindexLoading, setDeindexLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchConnections = async () => {
    try {
      const data = await catalogApi.listConnections();
      setConnections(data);
      if (data.length > 0 && !selectedConnectionId) {
        setSelectedConnectionId(data[0].id);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load connections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  useEffect(() => {
    if (!selectedConnectionId) {
      setEndpoints([]);
      return;
    }

    const fetchEndpoints = async () => {
      try {
        const eps = await catalogApi.getConnectionEndpoints(selectedConnectionId);
        setEndpoints(eps);
      } catch (err: any) {
        setErrorMessage(err.message || 'Failed to load catalog endpoints.');
      }
    };

    fetchEndpoints();
  }, [selectedConnectionId]);

  const handleIndexRAG = async (connectionId: string) => {
    setIndexing(true);
    setActionMessage(null);
    setErrorMessage(null);
    try {
      const res = await ragApi.indexConnection(connectionId);
      setActionMessage(`Successfully indexed ${res.indexed_count} endpoints into RAG Vector Store.`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to index connection in RAG.');
    } finally {
      setIndexing(false);
    }
  };

  const handleReindexRAG = async (connectionId: string) => {
    setReindexing(true);
    setActionMessage(null);
    setErrorMessage(null);
    try {
      const res = await ragApi.reindexConnection(connectionId);
      setActionMessage(`Successfully re-indexed ${res.indexed_count} endpoints in RAG Vector Store.`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to re-index connection in RAG.');
    } finally {
      setReindexing(false);
    }
  };

  const handleDeleteIndexRAG = async (connectionId: string) => {
    setDeindexLoading(true);
    setActionMessage(null);
    setErrorMessage(null);
    try {
      const res = await ragApi.deleteIndex(connectionId);
      setActionMessage(`Successfully deleted ${res.deleted_count} vectors from RAG store.`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete RAG index.');
    } finally {
      setDeindexLoading(false);
    }
  };

  const handleDeleteConnection = async (connectionId: string) => {
    if (!window.confirm('Are you sure you want to delete this API connection?')) return;

    try {
      await catalogApi.deleteConnection(connectionId);
      setActionMessage('API Connection deleted successfully.');
      setSelectedConnectionId(null);
      fetchConnections();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete connection.');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">API Catalog & Connections</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage registered API connections, view extracted endpoints, and control vector index state.
        </p>
      </div>

      {actionMessage && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-xs text-emerald-700 underline font-semibold">Dismiss</button>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Connection List Sidebar */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
              <Database className="w-4 h-4 text-sky-600" />
              <span>Connections ({connections.length})</span>
            </h2>
            <button onClick={fetchConnections} title="Refresh Connections" className="p-1 text-slate-400 hover:text-slate-600">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {loading ? (
            <p className="text-xs text-slate-400">Loading connections...</p>
          ) : connections.length === 0 ? (
            <div className="text-center py-6 border border-dashed border-slate-200 rounded-lg">
              <p className="text-xs text-slate-500">No active API connections.</p>
              <p className="text-xs text-slate-400 mt-1">Discover a spec first.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {connections.map((conn) => (
                <div
                  key={conn.id}
                  onClick={() => setSelectedConnectionId(conn.id)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-colors ${
                    selectedConnectionId === conn.id
                      ? 'bg-sky-50 border-sky-300 text-sky-900'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-bold truncate">{conn.name}</p>
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  </div>
                  <p className="text-xs font-mono text-slate-500 mt-1 truncate">{conn.base_url}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Connection Catalog Endpoints & RAG Controls */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          {!selectedConnectionId ? (
            <div className="text-center py-12 text-slate-400">
              <Layers className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p className="text-sm font-medium">Select an API connection to inspect its catalog</p>
            </div>
          ) : (
            <>
              {/* Header & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    {connections.find((c) => c.id === selectedConnectionId)?.name}
                  </h2>
                  <p className="text-xs font-mono text-slate-500">
                    {connections.find((c) => c.id === selectedConnectionId)?.base_url}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => handleIndexRAG(selectedConnectionId)}
                    disabled={indexing}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
                  >
                    <Cpu className="w-4 h-4" />
                    <span>{indexing ? 'Indexing...' : 'Index RAG'}</span>
                  </button>

                  <button
                    onClick={() => handleReindexRAG(selectedConnectionId)}
                    disabled={reindexing}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>{reindexing ? 'Reindexing...' : 'Re-index'}</span>
                  </button>

                  <button
                    onClick={() => handleDeleteIndexRAG(selectedConnectionId)}
                    disabled={deindexLoading}
                    className="px-3 py-1.5 bg-amber-50 text-amber-800 hover:bg-amber-100 text-xs font-semibold rounded-lg border border-amber-200"
                  >
                    <span>Clear Vector Index</span>
                  </button>

                  <button
                    onClick={() => handleDeleteConnection(selectedConnectionId)}
                    className="px-3 py-1.5 bg-red-50 text-red-700 hover:bg-red-100 text-xs font-semibold rounded-lg flex items-center space-x-1.5"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>

              {/* Endpoints Table */}
              <div>
                <h3 className="text-sm font-bold text-slate-800 mb-3">
                  Catalog Endpoints ({endpoints.length})
                </h3>

                {endpoints.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No endpoints found for this connection.</p>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                    {endpoints.map((ep) => (
                      <div key={ep.id} className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                        <div className="flex items-center justify-between font-mono">
                          <div className="flex items-center space-x-2">
                            <span className="px-2 py-0.5 font-bold uppercase rounded bg-slate-200 text-slate-800">
                              {ep.method}
                            </span>
                            <span className="font-bold text-slate-900">{ep.path}</span>
                          </div>
                          {ep.operation_id && (
                            <span className="text-slate-400 italic font-sans">{ep.operation_id}</span>
                          )}
                        </div>
                        {ep.summary && <p className="text-slate-600 font-sans">{ep.summary}</p>}
                        <div className="text-[10px] text-slate-400 font-mono">
                          ID: <span className="text-slate-600">{ep.id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
