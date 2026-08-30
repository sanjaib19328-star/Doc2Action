import React, { useState } from 'react';
import { agentApi } from '../../api/agent';
import { verificationApi } from '../../api/verification';
import { useApplication } from '../../context/ApplicationContext';
import { NoApplicationSelected } from '../../components/common/NoApplicationSelected';
import type { ActionProposalResponse } from '../../types/api';
import {
  Bot,
  Send,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Play,
  AlertCircle,
  Clock,
  Terminal,
  Server,
  Cpu,
  Layers,
  Loader2,
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  step?: string;
  decisionType?: string;
  searchResults?: any[];
  proposal?: ActionProposalResponse;
}

export const AgentPage: React.FC = () => {
  const { selectedApplication, selectedApplicationId, isLoading: appLoading } = useApplication();

  const [inputQuery, setQueryInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      sender: 'agent',
      text: 'Hello! I am your Doc2Action AI Agent. State your intent (e.g. "Find pets with status=available" or "Get customer orders"), and I will perform RAG catalog search within your active application, analyze missing parameters, and generate an Action Proposal for your human review.',
      timestamp: new Date().toLocaleTimeString(),
      step: 'IDLE',
      decisionType: 'INFORMATION',
    },
  ]);

  const [processing, setProcessing] = useState(false);
  const [paramInputs, setParamInputs] = useState<Record<string, string>>({});
  
  // Active Agent State from Backend
  const [currentStep, setCurrentStep] = useState<string>('IDLE');
  const [currentIntent, setCurrentIntent] = useState<string>('');
  const [selectedEndpoint, setSelectedEndpoint] = useState<any>(null);
  const [missingParams, setMissingParams] = useState<string[]>([]);
  const [extractedParams, setExtractedParams] = useState<Record<string, any>>({});
  const [activeProposal, setActiveProposal] = useState<ActionProposalResponse | null>(null);
  const [llmActive, setLlmActive] = useState<boolean>(false);

  if (!appLoading && !selectedApplicationId) {
    return <NoApplicationSelected moduleName="AI Agent Workspace" />;
  }

  const addMessage = (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMsg: ChatMessage = {
      ...msg,
      id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, newMsg]);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || processing || !selectedApplicationId) return;

    const userText = inputQuery.trim();
    setQueryInput('');
    setProcessing(true);

    addMessage({
      sender: 'user',
      text: userText,
    });

    try {
      const response = await agentApi.processQuery({
        query: userText,
        application_id: selectedApplicationId,
      });
      
      setLlmActive(response.llm_configured);
      setCurrentStep(response.step);
      if (response.intent) setCurrentIntent(response.intent);
      if (response.selected_endpoint) setSelectedEndpoint(response.selected_endpoint);
      setMissingParams(response.missing_parameters || []);
      setExtractedParams(response.extracted_parameters || {});
      if (response.proposal) setActiveProposal(response.proposal);

      addMessage({
        sender: 'agent',
        text: response.text_message,
        step: response.step,
        decisionType: response.decision_type,
        searchResults: response.rag_hits,
        proposal: response.proposal,
      });
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Error] ${err.message || 'Failed to process agent query.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
      setCurrentStep('FAILED');
    } finally {
      setProcessing(false);
    }
  };

  const handleProvideParameters = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEndpoint || processing || !selectedApplicationId) return;

    setProcessing(true);
    const paramSummary = Object.entries(paramInputs).map(([k, v]) => `${k}=${v}`).join(', ');
    const combinedQuery = `${currentIntent} with parameters ${paramSummary}`;

    addMessage({
      sender: 'user',
      text: `Provided parameters: ${JSON.stringify(paramInputs)}`,
    });

    try {
      const response = await agentApi.processQuery({
        query: combinedQuery,
        application_id: selectedApplicationId,
      });
      
      setCurrentStep(response.step);
      setMissingParams(response.missing_parameters || []);
      if (response.proposal) setActiveProposal(response.proposal);

      addMessage({
        sender: 'agent',
        text: response.text_message,
        step: response.step,
        decisionType: response.decision_type,
        proposal: response.proposal,
      });
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Error] ${err.message || 'Failed to submit parameters.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
      setCurrentStep('FAILED');
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirmProposal = async (proposalId: string) => {
    setProcessing(true);
    try {
      const confirmedProposal = await verificationApi.confirmProposal(proposalId);
      setActiveProposal(confirmedProposal);
      setCurrentStep('CONFIRMED');

      addMessage({
        sender: 'agent',
        text: `[Action Proposal Confirmed] Human confirmation registered for Proposal ID ${proposalId}. Ready for execution.`,
        step: 'CONFIRMED',
        proposal: confirmedProposal,
        decisionType: 'WAIT_FOR_CONFIRMATION',
      });
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Confirmation Failed] ${err.message || 'Failed to confirm proposal.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleRejectProposal = async (proposalId: string) => {
    setProcessing(true);
    try {
      const rejectedProposal = await verificationApi.rejectProposal(proposalId, {
        reason: 'User rejected in Agent workspace',
      });
      setActiveProposal(rejectedProposal);
      setCurrentStep('REJECTED');

      addMessage({
        sender: 'agent',
        text: `[Action Proposal Rejected] Proposal ID ${proposalId} has been rejected by user.`,
        step: 'REJECTED',
        proposal: rejectedProposal,
        decisionType: 'INFORMATION',
      });
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Rejection Failed] ${err.message || 'Failed to reject proposal.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleExecuteProposal = async (proposalId: string) => {
    setProcessing(true);
    try {
      addMessage({
        sender: 'agent',
        text: `[Executing Action] Sending request via backend execution engine...`,
        step: 'EXECUTING',
        decisionType: 'EXECUTE',
      });

      const execResultProposal = await verificationApi.executeProposal(proposalId);
      setActiveProposal(execResultProposal);
      setCurrentStep('COMPLETED');

      addMessage({
        sender: 'agent',
        text: `[Action Execution Complete] Status: ${execResultProposal.execution_result?.status?.toUpperCase()}\nTarget: ${execResultProposal.target_url}`,
        step: 'COMPLETED',
        proposal: execResultProposal,
        decisionType: 'RESULT',
      });
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Execution Failed] ${err.message || 'Failed to execute proposal.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
    } finally {
      setProcessing(false);
    }
  };

  const renderDecisionBadge = (type?: string) => {
    if (!type) return null;
    const badgeMap: Record<string, { label: string; color: string }> = {
      INFORMATION: { label: 'Info', color: 'bg-slate-100 text-slate-700 border-slate-200' },
      SEARCH_API: { label: 'RAG Search', color: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
      REQUEST_PARAMETERS: { label: 'Parameters Needed', color: 'bg-amber-100 text-amber-800 border-amber-200' },
      CREATE_PROPOSAL: { label: 'Action Proposed', color: 'bg-sky-100 text-sky-800 border-sky-200' },
      WAIT_FOR_CONFIRMATION: { label: 'Confirmation Required', color: 'bg-amber-100 text-amber-800 border-amber-200' },
      EXECUTE: { label: 'Executing', color: 'bg-blue-100 text-blue-800 border-blue-200' },
      RESULT: { label: 'Execution Result', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
      ERROR: { label: 'Error', color: 'bg-rose-100 text-rose-800 border-rose-200' },
    };

    const b = badgeMap[type] || { label: type, color: 'bg-slate-100 text-slate-700 border-slate-200' };

    return (
      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${b.color}`}>
        {b.label}
      </span>
    );
  };

  const renderStepBadge = (step?: string) => {
    if (!step || step === 'IDLE') return null;
    const badgeColors: Record<string, string> = {
      SEARCHING: 'bg-sky-100 text-sky-800 border-sky-200',
      PLANNING: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      WAITING_FOR_INPUT: 'bg-amber-100 text-amber-800 border-amber-200',
      WAITING_FOR_CONFIRMATION: 'bg-amber-100 text-amber-800 border-amber-200',
      CONFIRMED: 'bg-sky-100 text-sky-800 border-sky-200',
      EXECUTING: 'bg-blue-100 text-blue-800 border-blue-200',
      COMPLETED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      REJECTED: 'bg-rose-100 text-rose-800 border-rose-200',
      FAILED: 'bg-rose-100 text-rose-800 border-rose-200',
    };

    return (
      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${badgeColors[step] || 'bg-slate-100 text-slate-700'}`}>
        {step}
      </span>
    );
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">AI Agent Workspace</h1>
            {selectedApplication && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-sky-100 text-sky-800 tracking-wider flex items-center space-x-1">
                <Layers className="w-3 h-3 text-sky-600 mr-1" />
                {selectedApplication.name}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real Gemini LLM + RAG Knowledge Base + Human-in-the-Loop Action Proposal workflow inside application <span className="font-semibold text-slate-700">"{selectedApplication?.name}"</span>.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="px-3 py-1 bg-sky-50 text-sky-800 border border-sky-200 rounded-full text-xs font-semibold flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-sky-600" />
            <span>FastAPI Agent Core</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Feed */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col h-[680px]">
          {/* Header */}
          <div className="p-4 bg-slate-900 text-white rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-sky-500 flex items-center justify-center text-white font-bold text-xs shadow-xs">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-xs font-bold leading-tight">Doc2Action API Agent</h2>
                <p className="text-[10px] text-slate-400 font-mono">App Context: {selectedApplication?.name}</p>
              </div>
            </div>
            {renderStepBadge(currentStep)}
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-2xl p-4 rounded-2xl text-xs space-y-2.5 ${
                    m.sender === 'user'
                      ? 'bg-sky-600 text-white rounded-br-none shadow-xs'
                      : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] opacity-75 mb-1 font-mono">
                    <span className="font-bold uppercase flex items-center space-x-1">
                      <span>{m.sender}</span>
                      {m.decisionType && renderDecisionBadge(m.decisionType)}
                    </span>
                    <span>{m.timestamp}</span>
                  </div>

                  <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>

                  {/* RAG Search Hits context */}
                  {m.searchResults && m.searchResults.length > 0 && (
                    <div className="p-3 bg-white rounded-xl border border-slate-200 space-y-2 font-mono text-[11px] text-slate-700">
                      <p className="font-bold text-slate-900 flex items-center space-x-1">
                        <Server className="w-3.5 h-3.5 text-indigo-600" />
                        <span>RAG Context Candidates:</span>
                      </p>
                      {m.searchResults.map((hit, idx) => (
                        <div key={idx} className="p-2 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                          <span>[{hit.method}] {hit.path}</span>
                          <span className="text-indigo-600 font-bold">{(hit.score * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Action Proposal Card in Message Feed */}
                  {m.proposal && (
                    <div className="p-4 bg-amber-50/90 border border-amber-200 rounded-xl space-y-3 text-slate-900 font-sans">
                      <div className="flex items-center justify-between border-b border-amber-200 pb-2">
                        <span className="font-bold text-amber-900 flex items-center space-x-1">
                          <ShieldCheck className="w-4 h-4 text-amber-600" />
                          <span>Action Proposal #{m.proposal.proposal_id.substring(0, 8)}</span>
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-200 text-amber-900">
                          {m.proposal.status}
                        </span>
                      </div>

                      <div className="text-xs font-mono bg-white p-2.5 rounded-lg border border-amber-100 space-y-1">
                        <p><span className="text-slate-400">Method & URL:</span> <span className="font-bold text-slate-900">[{m.proposal.http_method}] {m.proposal.target_url}</span></p>
                        <p><span className="text-slate-400">Headers:</span> {JSON.stringify(m.proposal.headers)}</p>
                        {m.proposal.body && <p><span className="text-slate-400">Body:</span> {JSON.stringify(m.proposal.body)}</p>}
                      </div>

                      {/* Controls inside card */}
                      <div className="flex items-center justify-end space-x-2 pt-1">
                        {m.proposal.status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleConfirmProposal(m.proposal!.proposal_id)}
                              disabled={processing}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1 disabled:opacity-50 transition-colors shadow-xs"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Confirm Proposal</span>
                            </button>
                            <button
                              onClick={() => handleRejectProposal(m.proposal!.proposal_id)}
                              disabled={processing}
                              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1 disabled:opacity-50 transition-colors shadow-xs"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                              <span>Reject</span>
                            </button>
                          </>
                        )}

                        {m.proposal.status === 'confirmed' && (
                          <button
                            onClick={() => handleExecuteProposal(m.proposal!.proposal_id)}
                            disabled={processing}
                            className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1 disabled:opacity-50 transition-colors shadow-xs"
                          >
                            <Play className="w-3.5 h-3.5" />
                            <span>Execute Confirmed Action</span>
                          </button>
                        )}
                      </div>

                      {m.proposal.execution_result && (
                        <div className="p-3 bg-emerald-100/60 border border-emerald-200 rounded-lg text-xs font-mono space-y-1">
                          <p className="font-bold text-emerald-900">Execution Result:</p>
                          <pre className="p-2 bg-white rounded border border-emerald-200 text-slate-800 overflow-x-auto">
                            {JSON.stringify(m.proposal.execution_result, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Missing Parameter Input Form if waiting for input */}
          {currentStep === 'WAITING_FOR_INPUT' && missingParams.length > 0 && (
            <div className="p-4 bg-amber-50 border-t border-amber-200 space-y-3">
              <p className="text-xs font-bold text-amber-900 flex items-center space-x-1">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span>Required Parameters Needed:</span>
              </p>

              <form onSubmit={handleProvideParameters} className="space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {missingParams.map((param) => (
                    <div key={param}>
                      <label className="block text-[10px] font-bold text-slate-700 uppercase">{param}</label>
                      <input
                        type="text"
                        required
                        value={paramInputs[param] || ''}
                        onChange={(e) => setParamInputs({ ...paramInputs, [param]: e.target.value })}
                        placeholder={`Enter ${param}`}
                        className="w-full px-2.5 py-1.5 bg-white border border-amber-300 rounded-lg text-xs"
                      />
                    </div>
                  ))}
                </div>
                <button
                  type="submit"
                  disabled={processing}
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-lg shadow-xs disabled:opacity-50"
                >
                  Submit Parameters & Generate Proposal
                </button>
              </form>
            </div>
          )}

          {/* Chat Input Bar */}
          <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-200 flex gap-2">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Tell the agent what to do in this app (e.g. Find pets with status=available)..."
              disabled={processing}
              className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-sky-500 focus:bg-white"
            />
            <button
              type="submit"
              disabled={processing || !inputQuery.trim()}
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 disabled:opacity-50 transition-colors shadow-xs"
            >
              {processing ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
              <span>Send</span>
            </button>
          </form>
        </div>

        {/* Sidebar Context & State Inspection */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6">
          <div>
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3 flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-sky-600" />
              <span>Agent State Inspection</span>
            </h2>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">Application Context</span>
              <p className="font-bold text-slate-900 mt-1 font-sans flex items-center space-x-1">
                <Layers className="w-3.5 h-3.5 text-sky-600" />
                <span>{selectedApplication?.name}</span>
              </p>
            </div>

            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">Current Step</span>
              <div className="mt-1">{renderStepBadge(currentStep)}</div>
            </div>

            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">Backend Engine</span>
              <p className="font-bold text-slate-800 mt-0.5 flex items-center space-x-1 font-sans">
                <Cpu className="w-3.5 h-3.5 text-indigo-500" />
                <span>{llmActive ? 'Gemini LLM Active' : 'FastAPI RAG Agent Engine'}</span>
              </p>
            </div>

            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">Intent</span>
              <p className="font-semibold text-slate-900 mt-1 font-sans">{currentIntent || 'None'}</p>
            </div>

            {selectedEndpoint && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                <span className="text-slate-400 font-semibold block uppercase text-[10px]">Target Endpoint</span>
                <p className="font-bold text-slate-900">[{selectedEndpoint.method}] {selectedEndpoint.path}</p>
                <p className="text-[10px] text-slate-500 font-sans">{selectedEndpoint.summary || selectedEndpoint.id}</p>
              </div>
            )}

            {extractedParams && Object.keys(extractedParams).length > 0 && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                <span className="text-slate-400 font-semibold block uppercase text-[10px]">Extracted Parameters</span>
                <pre className="text-[10px] text-slate-700 font-mono whitespace-pre-wrap">{JSON.stringify(extractedParams, null, 2)}</pre>
              </div>
            )}

            {activeProposal && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl space-y-1">
                <span className="text-amber-800 font-semibold block uppercase text-[10px]">Active Proposal ID</span>
                <p className="font-bold text-amber-950 truncate">{activeProposal.proposal_id}</p>
                <p className="text-[10px] text-amber-700">Expires: {new Date(activeProposal.expires_at).toLocaleTimeString()}</p>
              </div>
            )}
          </div>

          <div className="p-4 bg-sky-50/60 border border-sky-100 rounded-xl text-xs space-y-2">
            <p className="font-bold text-sky-900 flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              <span>Human-in-the-Loop Mandate</span>
            </p>
            <p className="text-slate-600 leading-relaxed font-sans text-[11px]">
              Doc2Action Agent operates strictly on the active application's catalog and will never execute requests autonomously.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
