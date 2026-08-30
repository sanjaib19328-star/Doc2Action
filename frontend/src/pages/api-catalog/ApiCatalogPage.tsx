import React, { useEffect, useState, useCallback } from 'react';
import { catalogApi } from '../../api/catalog';
import { ragApi } from '../../api/rag';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { APIConnection, APIEndpoint } from '../../types/api';
import { Database, Trash2, Layers, Cpu, CheckCircle2, AlertCircle, RefreshCw, ExternalLink, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ApiCatalogPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [deindexLoading, setDeindexLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchConnections = useCallback(async () => {
    if (!selectedApplicationId) {
      setConnections([]);
      setSelectedConnectionId(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const data = await catalogApi.listConnections(selectedApplicationId);
      setConnections(data);
      if (data.length > 0) {
        setSelectedConnectionId((prev) => (data.some((c) => c.id === prev) ? prev : data[0].id));
      } else {
        setSelectedConnectionId(null);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load connections.');
    } finally {
      setLoading(false);
    }
  }, [selectedApplicationId]);

  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

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

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="API Catalog" />;
  }

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
      fetchConnections();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete connection.');
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">API Catalog & Connections</h1>
            {selectedApplication && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
                <Layers className="w-3 h-3 text-sky-600 mr-1" />
                {selectedApplication.name}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Manage registered API connections, view extracted endpoints, and control vector index state for this application.
          </p>
        </div>
      </div>

      {actionMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center justify-between animate-in fade-in duration-200">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-xs text-emerald-700 underline font-semibold">Dismiss</button>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-center space-x-2 animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Connection List Sidebar */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
              <Database className="w-4 h-4 text-sky-600" />
              <span>Connections ({connections.length})</span>
            </h2>
            <button onClick={fetchConnections} title="Refresh Connections" className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {loading ? (
            <div className="text-center py-6">
              <Loader2 className="w-5 h-5 animate-spin text-slate-400 mx-auto" />
              <p className="text-[11px] text-slate-400 mt-1">Loading connections...</p>
            </div>
          ) : connections.length === 0 ? (
            <div className="text-center py-6 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
              <p className="text-xs text-slate-500 font-semibold">No active API connections.</p>
              <p className="text-[10px] text-slate-400 mt-1">Discover a spec first.</p>
              <Link
                to="/api-discovery"
                className="inline-flex items-center px-3 py-1.5 mt-3 text-xs font-semibold text-white bg-sky-600 rounded-lg hover:bg-sky-500"
              >
                Discover Specs
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {connections.map((conn) => (
                <div
                  key={conn.id}
                  onClick={() => setSelectedConnectionId(conn.id)}
                  className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                    selectedConnectionId === conn.id
                      ? 'bg-sky-50 border-sky-300 text-sky-900 shadow-xs'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-bold truncate">{conn.name}</p>
                    <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                  </div>
                  <p className="text-[10px] font-mono text-slate-500 mt-1 truncate">{conn.base_url}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Connection Catalog Endpoints & RAG Controls */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
          {!selectedConnectionId ? (
            <div className="text-center py-16 text-slate-400">
              <Database className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <p className="text-xs font-medium">Select an API connection to inspect its catalog</p>
            </div>
          ) : (
            <>
              {/* Header & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-black text-slate-900">
                      {connections.find((c) => c.id === selectedConnectionId)?.name}
                    </h2>
                    <Link
                      to={`/api-catalog/${selectedConnectionId}`}
                      className="text-xs text-sky-600 hover:text-sky-700 font-semibold flex items-center"
                      title="Open full connection page"
                    >
                      <span>Full View</span>
                      <ExternalLink className="w-3.5 h-3.5 ml-1" />
                    </Link>
                  </div>
                  <p className="text-xs font-mono text-slate-500 mt-0.5">
                    {connections.find((c) => c.id === selectedConnectionId)?.base_url}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => handleIndexRAG(selectedConnectionId)}
                    disabled={indexing}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-xs flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
                  >
                    <Cpu className="w-3.5 h-3.5" />
                    <span>{indexing ? 'Indexing...' : 'Index RAG'}</span>
                  </button>

                  <button
                    onClick={() => handleReindexRAG(selectedConnectionId)}
                    disabled={reindexing}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl shadow-xs flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>{reindexing ? 'Reindexing...' : 'Re-index'}</span>
                  </button>

                  <button
                    onClick={() => handleDeleteIndexRAG(selectedConnectionId)}
                    disabled={deindexLoading}
                    className="px-3 py-1.5 bg-amber-50 text-amber-800 hover:bg-amber-100 text-xs font-semibold rounded-xl border border-amber-200 transition-colors"
                  >
                    <span>Clear Vectors</span>
                  </button>

                  <button
                    onClick={() => handleDeleteConnection(selectedConnectionId)}
                    className="px-3 py-1.5 bg-rose-50 text-rose-700 hover:bg-rose-100 text-xs font-semibold rounded-xl border border-rose-200 flex items-center space-x-1 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>

              {/* Endpoints Table */}
              <div>
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3">
                  Catalog Endpoints ({endpoints.length})
                </h3>

                {endpoints.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No endpoints found for this connection.</p>
                ) : (
                  <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                    {endpoints.map((ep) => (
                      <div key={ep.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1.5">
                        <div className="flex items-center justify-between font-mono">
                          <div className="flex items-center space-x-2">
                            <span className="px-1.5 py-0.5 font-bold uppercase rounded bg-slate-200 text-slate-800 text-[10px]">
                              {ep.method}
                            </span>
                            <span className="font-bold text-slate-900">{ep.path}</span>
                          </div>
                          {ep.operation_id && (
                            <span className="text-slate-400 italic font-sans text-[11px]">{ep.operation_id}</span>
                          )}
                        </div>
                        {ep.summary && <p className="text-slate-600 font-sans text-[11px]">{ep.summary}</p>}
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
