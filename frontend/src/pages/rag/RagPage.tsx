import React, { useEffect, useState } from 'react';
import { ragApi } from '../../api/rag';
import { catalogApi } from '../../api/catalog';
import type { RAGSearchResult, APIConnection } from '../../types/api';
import { Server, Search, Sparkles, AlertCircle, Filter } from 'lucide-react';

export const RagPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [topK, setTopK] = useState<number>(5);

  const [results, setResults] = useState<RAGSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    catalogApi.listConnections().then(setConnections).catch(() => []);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setError(null);
    setLoading(true);
    setSearched(true);

    try {
      const hits = await ragApi.search({
        query: query.trim(),
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">RAG Knowledge Base & Semantic Search</h1>
        <p className="text-sm text-slate-500 mt-1">
          Perform semantic vector similarity search across indexed API endpoints to retrieve contextual operation specs for the AI agent.
        </p>
      </div>

      {/* Semantic Search Box */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Natural Language API Search Query
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search className="w-5 h-5" />
              </div>
              <input
                type="text"
                required
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. process refund, create new user, search charges"
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white text-sm"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-slate-100">
            <div className="flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-slate-400" />
                <span className="font-semibold text-slate-600">Filter Connection:</span>
                <select
                  value={selectedConnectionId}
                  onChange={(e) => setSelectedConnectionId(e.target.value)}
                  className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="">All Connections</option>
                  {connections.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-600">Top Results (K):</span>
                <select
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="px-2 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Searching Vectors...' : 'Semantic Search'}</span>
            </button>
          </div>
        </form>

        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Search Results */}
      {searched && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Server className="w-5 h-5 text-indigo-600" />
            <span>Retrieval Context Results ({results.length})</span>
          </h2>

          {results.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-lg text-slate-400">
              <p className="text-sm font-medium">No matching API endpoints found in RAG store</p>
              <p className="text-xs mt-1">Make sure your API connection is indexed in the API Catalog page.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((hit, idx) => (
                <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-2 gap-2">
                    <div className="flex items-center space-x-2 font-mono text-xs">
                      <span className="px-2 py-0.5 font-bold uppercase rounded bg-indigo-100 text-indigo-900">
                        {hit.method}
                      </span>
                      <span className="font-bold text-slate-900">{hit.path}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-slate-500 font-semibold">{hit.connection_name}</span>
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-200 text-slate-700">
                        Score: {(hit.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <pre className="text-xs font-mono text-slate-700 bg-white p-3 rounded border border-slate-200 overflow-x-auto whitespace-pre-wrap">
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
