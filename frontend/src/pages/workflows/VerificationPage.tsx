import React, { useEffect, useState, useCallback } from 'react';
import { verificationApi } from '../../api/verification';
import { catalogApi } from '../../api/catalog';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { ActionProposalResponse, APIConnection, APIEndpoint } from '../../types/api';
import { ShieldCheck, CheckCircle2, XCircle, Play, AlertCircle, Plus, Layers, Loader2 } from 'lucide-react';

export const VerificationPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [proposals, setProposals] = useState<ActionProposalResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Proposal Creation Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [connections, setConnections] = useState<APIConnection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>('');
  const [endpoints, setEndpoints] = useState<APIEndpoint[]>([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState<string>('');

  const [intentSummary, setIntentSummary] = useState('');
  const [pathParams, setPathParams] = useState('{}');
  const [queryParams, _setQueryParams] = useState('{}');
  const [body, setBody] = useState('{}');
  const [creating, setCreating] = useState(false);

  const fetchProposals = useCallback(async () => {
    if (!selectedApplicationId) {
      setProposals([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await verificationApi.listProposals(selectedApplicationId);
      setProposals(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load action proposals.');
    } finally {
      setLoading(false);
    }
  }, [selectedApplicationId]);

  useEffect(() => {
    fetchProposals();
    if (selectedApplicationId) {
      catalogApi.listConnections(selectedApplicationId).then((conns) => {
        setConnections(conns);
        if (conns.length > 0) setSelectedConnectionId(conns[0].id);
      }).catch(() => []);
    }
  }, [fetchProposals, selectedApplicationId]);

  useEffect(() => {
    if (!selectedConnectionId) {
      setEndpoints([]);
      setSelectedEndpointId('');
      return;
    }
    catalogApi.getConnectionEndpoints(selectedConnectionId).then((eps) => {
      setEndpoints(eps);
      if (eps.length > 0) setSelectedEndpointId(eps[0].id);
      else setSelectedEndpointId('');
    }).catch(() => []);
  }, [selectedConnectionId]);

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="Human-in-the-Loop Verification" />;
  }

  const handleCreateProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEndpointId || !selectedApplicationId) return;

    setCreating(true);
    setErrorMessage(null);
    try {
      const pParams = JSON.parse(pathParams || '{}');
      const qParams = JSON.parse(queryParams || '{}');
      const bPayload = JSON.parse(body || '{}');

      await verificationApi.propose({
        endpoint_id: selectedEndpointId,
        application_id: selectedApplicationId,
        intent_summary: intentSummary,
        path_params: pParams,
        query_params: qParams,
        body: Object.keys(bPayload).length > 0 ? bPayload : undefined,
      });

      setActionMessage('New Action Proposal created successfully.');
      setModalOpen(false);
      setIntentSummary('');
      fetchProposals();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create proposal.');
    } finally {
      setCreating(false);
    }
  };

  const handleConfirm = async (id: string) => {
    setProcessingId(id);
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await verificationApi.confirmProposal(id);
      setActionMessage(`Action proposal confirmed! Ready for execution.`);
      fetchProposals();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to confirm proposal.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: string) => {
    setProcessingId(id);
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await verificationApi.rejectProposal(id);
      setActionMessage(`Action proposal rejected.`);
      fetchProposals();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reject proposal.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleExecute = async (id: string) => {
    setProcessingId(id);
    setActionMessage(null);
    setErrorMessage(null);
    try {
      const res = await verificationApi.executeProposal(id);
      setActionMessage(`Action executed successfully! Status: ${res.execution_result?.status}`);
      fetchProposals();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to execute proposal.');
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">Pending Review</span>;
      case 'confirmed':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-100 text-sky-800">Confirmed</span>;
      case 'executed':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">Executed</span>;
      case 'rejected':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800">Rejected</span>;
      case 'expired':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-200 text-slate-700">Expired</span>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Human-in-the-Loop Verification</h1>
            {selectedApplication && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
                <Layers className="w-3 h-3 text-sky-600 mr-1" />
                {selectedApplication.name}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Review, confirm, or reject proposed API operations prior to execution in application <span className="font-semibold text-slate-700">"{selectedApplication?.name}"</span>.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center justify-center space-x-1.5 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Action Proposal</span>
        </button>
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

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-sky-600" />
          <span>Action Proposals ({proposals.length})</span>
        </h2>

        {loading ? (
          <div className="text-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400 mx-auto" />
            <p className="text-xs text-slate-400 mt-2">Loading action proposals...</p>
          </div>
        ) : proposals.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-slate-400">
            <p className="text-xs font-semibold text-slate-600">No action proposals found for this application</p>
            <p className="text-[11px] text-slate-400 mt-0.5">Use the AI Agent or click New Action Proposal to create one.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {proposals.map((prop) => (
              <div key={prop.proposal_id} className="p-5 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-3 gap-2">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-200 text-slate-900 font-mono">
                      {prop.http_method}
                    </span>
                    <h3 className="text-xs font-bold text-slate-900">{prop.intent_summary}</h3>
                  </div>
                  <div>{getStatusBadge(prop.status)}</div>
                </div>

                <div className="text-xs font-mono bg-white p-3 rounded-xl border border-slate-200 space-y-1">
                  <p><span className="text-slate-400">Target URL:</span> <span className="text-slate-900 font-semibold">{prop.target_url}</span></p>
                  {prop.body && (
                    <p><span className="text-slate-400">Body Payload:</span> <span className="text-slate-700">{JSON.stringify(prop.body)}</span></p>
                  )}
                  <p><span className="text-slate-400">Masked Headers:</span> <span className="text-slate-700">{JSON.stringify(prop.headers)}</span></p>
                  <p><span className="text-slate-400">Expires At:</span> <span className="text-slate-600">{new Date(prop.expires_at).toLocaleString()}</span></p>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end space-x-2 pt-2">
                  {prop.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleConfirm(prop.proposal_id)}
                        disabled={processingId === prop.proposal_id}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1 transition-colors shadow-xs"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Confirm</span>
                      </button>
                      <button
                        onClick={() => handleReject(prop.proposal_id)}
                        disabled={processingId === prop.proposal_id}
                        className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1 transition-colors shadow-xs"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </>
                  )}

                  {prop.status === 'confirmed' && (
                    <button
                      onClick={() => handleExecute(prop.proposal_id)}
                      disabled={processingId === prop.proposal_id}
                      className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1 transition-colors shadow-xs"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Execute Action</span>
                    </button>
                  )}
                </div>

                {/* Execution Result payload if executed */}
                {prop.execution_result && (
                  <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs space-y-1 font-mono">
                    <p className="font-bold text-emerald-900">Execution Result:</p>
                    <pre className="text-slate-800 bg-white p-2.5 rounded-lg border border-emerald-100 overflow-x-auto">
                      {JSON.stringify(prop.execution_result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Proposal Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4 border border-slate-200 animate-in zoom-in-95 duration-150">
            <h3 className="text-base font-bold text-slate-900">Create Action Proposal</h3>
            <p className="text-xs text-slate-500">
              Create an action proposal inside application <span className="font-semibold text-sky-700">"{selectedApplication?.name}"</span>.
            </p>

            <form onSubmit={handleCreateProposal} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Intent Summary</label>
                <input
                  type="text"
                  required
                  value={intentSummary}
                  onChange={(e) => setIntentSummary(e.target.value)}
                  placeholder="e.g. Refund charge ch_123 for $50"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">API Connection</label>
                <select
                  value={selectedConnectionId}
                  onChange={(e) => setSelectedConnectionId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs"
                >
                  {connections.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Catalog Endpoint</label>
                <select
                  value={selectedEndpointId}
                  onChange={(e) => setSelectedEndpointId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono"
                >
                  {endpoints.map((ep) => (
                    <option key={ep.id} value={ep.id}>[{ep.method}] {ep.path}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Path Params (JSON)</label>
                <input
                  type="text"
                  value={pathParams}
                  onChange={(e) => setPathParams(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Body Payload (JSON)</label>
                <input
                  type="text"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-mono"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Proposal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
