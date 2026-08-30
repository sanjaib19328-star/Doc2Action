import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { catalogApi } from '../../api/catalog';
import { ragApi } from '../../api/rag';
import type { APIConnectionDetail } from '../../types/api';
import { Database, ArrowLeft, Cpu, RefreshCw, Trash2, AlertCircle, CheckCircle2, Server, Shield } from 'lucide-react';

export const ConnectionDetailPage: React.FC = () => {
  const { connectionId } = useParams<{ connectionId: string }>();
  const navigate = useNavigate();

  const [connection, setConnection] = useState<APIConnectionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [deindexLoading, setDeindexLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchConnection = async () => {
    if (!connectionId) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await catalogApi.getConnection(connectionId);
      setConnection(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load connection details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnection();
  }, [connectionId]);

  const handleIndexRAG = async () => {
    if (!connectionId) return;
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

  const handleReindexRAG = async () => {
    if (!connectionId) return;
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

  const handleDeleteIndexRAG = async () => {
    if (!connectionId) return;
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

  const handleDeleteConnection = async () => {
    if (!connectionId) return;
    if (!window.confirm('Are you sure you want to delete this API connection and its catalog?')) return;

    try {
      await catalogApi.deleteConnection(connectionId);
      navigate('/api-catalog');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete connection.');
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        <p className="text-sm">Loading API Connection details...</p>
      </div>
    );
  }

  if (errorMessage && !connection) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-800 space-y-4">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="font-semibold">{errorMessage}</span>
        </div>
        <Link to="/api-catalog" className="inline-flex items-center text-xs text-red-700 underline font-bold">
          <ArrowLeft className="w-4 h-4 mr-1" /> Return to API Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Link to="/api-catalog" className="p-2 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{connection?.name}</h1>
          <p className="text-xs font-mono text-slate-500">{connection?.base_url}</p>
        </div>
      </div>

      {actionMessage && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-xs text-emerald-700 underline font-semibold">
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Control Panel */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-sky-50 text-sky-600 rounded-lg">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-slate-400">Connection ID</p>
              <p className="text-xs font-mono text-slate-800 font-bold">{connection?.id}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleIndexRAG}
              disabled={indexing}
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
            >
              <Cpu className="w-4 h-4" />
              <span>{indexing ? 'Indexing...' : 'Index RAG Store'}</span>
            </button>

            <button
              onClick={handleReindexRAG}
              disabled={reindexing}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
            >
              <RefreshCw className="w-4 h-4" />
              <span>{reindexing ? 'Reindexing...' : 'Re-index'}</span>
            </button>

            <button
              onClick={handleDeleteIndexRAG}
              disabled={deindexLoading}
              className="px-3.5 py-2 bg-amber-50 text-amber-800 hover:bg-amber-100 text-xs font-semibold rounded-lg border border-amber-200"
            >
              <span>Clear RAG Index</span>
            </button>

            <button
              onClick={handleDeleteConnection}
              className="px-3.5 py-2 bg-red-50 text-red-700 hover:bg-red-100 text-xs font-semibold rounded-lg flex items-center space-x-1.5"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete Connection</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono bg-slate-50 p-4 rounded-lg">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Specification ID</span>
            <span className="font-bold text-slate-800 truncate block">{connection?.specification_id}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Auth Configuration</span>
            <span className="font-bold text-slate-800 uppercase">{connection?.auth_config?.type || 'None'}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Created At</span>
            <span className="font-bold text-slate-800">{connection?.created_at ? new Date(connection.created_at).toLocaleString() : 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Catalog Endpoints List */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
          <Server className="w-5 h-5 text-sky-600" />
          <span>Extracted Catalog Endpoints ({connection?.endpoints?.length || 0})</span>
        </h2>

        {(!connection?.endpoints || connection.endpoints.length === 0) ? (
          <div className="text-center py-8 border border-dashed border-slate-200 rounded-lg text-slate-400 text-xs">
            No extracted endpoints found for this connection.
          </div>
        ) : (
          <div className="space-y-3">
            {connection.endpoints.map((ep) => (
              <div key={ep.id} className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                <div className="flex items-center justify-between font-mono">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 font-bold uppercase rounded bg-slate-200 text-slate-900">
                      {ep.method}
                    </span>
                    <span className="font-bold text-slate-900">{ep.path}</span>
                  </div>
                  {ep.operation_id && (
                    <span className="text-slate-400 italic font-sans">{ep.operation_id}</span>
                  )}
                </div>
                {ep.summary && <p className="text-slate-600 font-sans">{ep.summary}</p>}
                <div className="flex items-center space-x-4 text-[10px] text-slate-400 font-mono pt-1">
                  <span>Endpoint ID: <strong className="text-slate-700">{ep.id}</strong></span>
                  <span>Parameters: <strong className="text-slate-700">{ep.parameters?.length || 0}</strong></span>
                  <span className="flex items-center space-x-1">
                    <Shield className="w-3 h-3 text-indigo-500" />
                    <span>Security Requirements: {ep.security_requirements?.length || 0}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
