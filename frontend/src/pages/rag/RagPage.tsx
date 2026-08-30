import React, { useEffect, useState, useCallback } from 'react';
import { ragApi } from '../../api/rag';
import { catalogApi } from '../../api/catalog';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { RAGSearchResult, APIConnection } from '../../types/api';
import { Server, Search, Sparkles, AlertCircle, Filter, Layers, Loader2 } from 'lucide-react';

export const RagPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [query, setQuery] = useState('');
  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [topK, setTopK] = useState<number>(5);

  const [results, setResults] = useState<RAGSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const loadConnections = useCallback(async () => {
    if (!selectedApplicationId) {
      setConnections([]);
      return;
    }
    try {
      const data = await catalogApi.listConnections(selectedApplicationId);
      setConnections(data);
    } catch {
      setConnections([]);
    }
  }, [selectedApplicationId]);

  useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="RAG Knowledge Base & Semantic Search" />;
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !selectedApplicationId) return;

    setError(null);
    setLoading(true);
    setSearched(true);

    try {
      const hits = await ragApi.search({
        query: query.trim(),
        application_id: selectedApplicationId,
        connection_id: selectedConnectionId || undefined,
        top_k: topK,
      });
      setResults(hits);
    } catch (err: any) {
      setError(err.message || 'Failed to search RAG knowledge base.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">RAG Knowledge Base & Semantic Search</h1>
            {selectedApplication && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
                <Layers className="w-3 h-3 text-sky-600 mr-1" />
                {selectedApplication.name}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Perform semantic vector similarity search across indexed API endpoints for this application to retrieve contextual operation specs for the AI agent.
          </p>
        </div>
      </div>

      {/* Semantic Search Box */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Natural Language API Search Query
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                required
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. find pets by status, process refund, create charge"
                className="block w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-sky-500 focus:bg-white text-xs transition-all"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-slate-100">
            <div className="flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center space-x-2">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-semibold text-slate-600 text-[11px]">Filter Connection:</span>
                <select
                  value={selectedConnectionId}
                  onChange={(e) => setSelectedConnectionId(e.target.value)}
                  className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs"
                >
                  <option value="">All App Connections ({connections.length})</option>
                  {connections.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-600 text-[11px]">Top Results (K):</span>
                <select
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="px-2 py-1.5 bg-slate-50 border border-slate-300 rounded-xl text-xs"
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="w-full sm:w-auto px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Searching Vectors...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Semantic Search</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-center space-x-2 animate-in fade-in duration-200">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Search Results */}
      {searched && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <Server className="w-4 h-4 text-sky-600" />
            <span>Retrieval Context Results ({results.length})</span>
          </h2>

          {results.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-slate-400">
              <p className="text-xs font-semibold text-slate-600">No matching API endpoints found in RAG store for this application.</p>
              <p className="text-[11px] text-slate-400 mt-1">Make sure your API connection is indexed on the API Catalog page.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((hit, idx) => (
                <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-2 gap-2">
                    <div className="flex items-center space-x-2 font-mono text-xs">
                      <span className="px-1.5 py-0.5 font-bold uppercase rounded bg-sky-100 text-sky-900 text-[10px]">
                        {hit.method}
                      </span>
                      <span className="font-bold text-slate-900">{hit.path}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-slate-500 font-semibold">{hit.connection_name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-700">
                        Score: {(hit.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <pre className="text-xs font-mono text-slate-700 bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto whitespace-pre-wrap">
                    {hit.content}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
