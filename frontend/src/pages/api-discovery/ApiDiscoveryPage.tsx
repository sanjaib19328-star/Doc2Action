import React, { useEffect, useState } from 'react';
import { openApiApi } from '../../api/openapi';
import { catalogApi } from '../../api/catalog';
import type { APISpecification, APISpecificationDetail } from '../../types/api';
import { Globe, AlertCircle, CheckCircle2, ArrowRight, Server, Plus, FileText, ExternalLink } from 'lucide-react';

export const ApiDiscoveryPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [_, setDiscoveredSpec] = useState<APISpecificationDetail | null>(null);

  const [specs, setSpecs] = useState<APISpecification[]>([]);
  const [specsLoading, setSpecsLoading] = useState(true);
  const [selectedSpecDetail, setSelectedSpecDetail] = useState<APISpecificationDetail | null>(null);

  // Modal for creating catalog connection directly from discovered spec
  const [connectionModalOpen, setConnectionModalOpen] = useState(false);
  const [connectionName, setConnectionName] = useState('');
  const [authType, setAuthType] = useState('none');
  const [authToken, setAuthTypeToken] = useState('');
  const [creatingConnection, setCreatingConnection] = useState(false);

  const loadSpecs = async () => {
    try {
      const data = await openApiApi.listSpecifications();
      setSpecs(data);
    } catch {
      // Ignore initial load error
    } finally {
      setSpecsLoading(false);
    }
  };

  useEffect(() => {
    loadSpecs();
  }, []);

  const handleDiscover = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setDiscoveredSpec(null);

    if (!url.trim()) {
      setError('Please provide a valid OpenAPI or Swagger spec URL.');
      return;
    }

    setLoading(true);

    try {
      const result = await openApiApi.discover({ url: url.trim() });
      setDiscoveredSpec(result);
      setSelectedSpecDetail(result);
      setConnectionName(result.title);
      setSuccessMsg(`Specification '${result.title}' discovered and normalized successfully!`);
      loadSpecs();
    } catch (err: any) {
      setError(err.message || 'Failed to discover OpenAPI specification from provided URL.');
    } finally {
      setLoading(false);
    }
  };

  const handleInspectSpec = async (specId: string) => {
    try {
      const detail = await openApiApi.getSpecification(specId);
      setSelectedSpecDetail(detail);
      setConnectionName(detail.title);
    } catch (err: any) {
      setError(err.message || 'Failed to load specification details.');
    }
  };

  const handleCreateConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSpecDetail) return;

    setCreatingConnection(true);
    setError(null);
    try {
      const authConfig: Record<string, any> = {};
      if (authType === 'bearer') {
        authConfig.type = 'bearer';
        authConfig.token = authToken;
      }

      await catalogApi.createConnection({
        specification_id: selectedSpecDetail.id,
        name: connectionName || selectedSpecDetail.title,
        base_url: selectedSpecDetail.base_url || undefined,
        auth_config: authConfig,
      });

      setSuccessMsg(`API Connection '${connectionName || selectedSpecDetail.title}' created in API Catalog!`);
      setConnectionModalOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create API connection in catalog.');
    } finally {
      setCreatingConnection(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">OpenAPI & Swagger Discovery</h1>
        <p className="text-sm text-slate-500 mt-1">
          Ingest, validate, and normalize public or external API specifications against Server-Side Request Forgery (SSRF) protections.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-xs text-emerald-700 underline font-semibold">Dismiss</button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Discovery Input Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <form onSubmit={handleDiscover} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700">
              OpenAPI / Swagger Specification URL
            </label>
            <p className="text-xs text-slate-500 mb-2">
              Enter a publicly accessible JSON or YAML specification URL (e.g., https://petstore.swagger.io/v2/swagger.json).
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Globe className="w-5 h-5" />
                </div>
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://petstore.swagger.io/v2/swagger.json"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white text-sm"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm rounded-lg shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Discovering...' : 'Discover API'}
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Previously Discovered Specs List */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2 border-b border-slate-100 pb-3">
            <FileText className="w-4 h-4 text-sky-600" />
            <span>Discovered Specs ({specs.length})</span>
          </h2>

          {specsLoading ? (
            <p className="text-xs text-slate-400">Loading discovered specs...</p>
          ) : specs.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-slate-200 rounded-lg">
              <p className="text-xs text-slate-500">No specifications ingested yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {specs.map((s) => (
                <div
                  key={s.id}
                  onClick={() => handleInspectSpec(s.id)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-colors ${
                    selectedSpecDetail?.id === s.id
                      ? 'bg-sky-50 border-sky-300 text-sky-900'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-bold truncate">{s.title}</p>
                    <span className="px-1.5 py-0.5 text-[10px] font-bold bg-slate-200 text-slate-700 rounded">
                      v{s.spec_version}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-slate-500 mt-1 truncate">{s.source_url}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Specification Detail & Connect Action */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          {!selectedSpecDetail ? (
            <div className="text-center py-16 text-slate-400">
              <Server className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p className="text-sm font-medium">Discover a new spec or select an existing one to inspect details</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-xl font-bold text-slate-900">{selectedSpecDetail.title}</h2>
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800">
                      OpenAPI {selectedSpecDetail.spec_version}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{selectedSpecDetail.description || 'No description provided.'}</p>
                </div>

                <button
                  onClick={() => setConnectionModalOpen(true)}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs rounded-lg shadow-sm flex items-center justify-center space-x-1.5"
                >
                  <Plus className="w-4 h-4" />
                  <span>Connect to API Catalog</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs bg-slate-50 p-4 rounded-lg border border-slate-100 font-mono">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold block uppercase">API Version</span>
                  <span className="font-bold text-slate-800">{selectedSpecDetail.version}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold block uppercase">Base URL</span>
                  <span className="font-bold text-slate-800 truncate block">{selectedSpecDetail.base_url || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold block uppercase">Source URL</span>
                  <a href={selectedSpecDetail.source_url} target="_blank" rel="noreferrer" className="text-sky-600 hover:underline flex items-center space-x-1 truncate">
                    <span className="truncate">{selectedSpecDetail.source_url}</span>
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                </div>
              </div>

              {/* Operations List */}
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">
                  Extracted Endpoints ({selectedSpecDetail.operations.length})
                </h3>
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {selectedSpecDetail.operations.map((op) => (
                    <div key={op.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center space-x-3">
                        <span className="px-2 py-0.5 rounded font-bold uppercase bg-slate-200 text-slate-800">
                          {op.method}
                        </span>
                        <span className="text-slate-900 font-bold">{op.path}</span>
                      </div>
                      <span className="text-slate-500 font-sans italic truncate max-w-xs">{op.summary || op.operation_id || 'No summary'}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Connect Modal */}
      {connectionModalOpen && selectedSpecDetail && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900">Create API Connection</h3>
            <p className="text-xs text-slate-500">
              Connect <span className="font-semibold text-slate-800">{selectedSpecDetail.title}</span> to your API Catalog for RAG indexing and execution.
            </p>

            <form onSubmit={handleCreateConnection} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase">Connection Name</label>
                <input
                  type="text"
                  required
                  value={connectionName}
                  onChange={(e) => setConnectionName(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase">Authentication Type</label>
                <select
                  value={authType}
                  onChange={(e) => setAuthType(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="none">None / Public API</option>
                  <option value="bearer">Bearer JWT Token</option>
                </select>
              </div>

              {authType === 'bearer' && (
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase">Bearer Token Value</label>
                  <input
                    type="password"
                    required
                    value={authToken}
                    onChange={(e) => setAuthTypeToken(e.target.value)}
                    placeholder="sk_test_..."
                    className="mt-1 block w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono"
                  />
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setConnectionModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingConnection}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg disabled:opacity-50"
                >
                  {creatingConnection ? 'Connecting...' : 'Create Connection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
