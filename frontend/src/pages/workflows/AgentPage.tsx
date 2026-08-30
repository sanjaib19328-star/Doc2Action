import React, { useState } from 'react';
import { agentPlanner, AgentPlanner } from '../../agent/planner';
import { agentTools } from '../../agent/tools';
import { geminiClient } from '../../agent/client';
import type { AgentConversationState, ChatMessage, AgentStep, AgentDecisionType } from '../../agent/types';
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
  Key,
  Cpu
} from 'lucide-react';

export const AgentPage: React.FC = () => {
  const [inputQuery, setQueryInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      sender: 'agent',
      text: 'Hello! I am your Doc2Action AI Agent. State your intent (e.g., "Process refund for charge ch_123 for $50" or "Get customer profile usr_999"), and I will perform RAG catalog search, analyze missing parameters, and generate an Action Proposal for your human review.',
      timestamp: new Date().toLocaleTimeString(),
      step: 'IDLE',
      decisionType: 'INFORMATION',
    },
  ]);

  const [state, setState] = useState<AgentConversationState>(
    AgentPlanner.createInitialState()
  );
  const [processing, setProcessing] = useState(false);
  const [paramInputs, setParamInputs] = useState<Record<string, string>>({});

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
    if (!inputQuery.trim() || processing) return;

    const userText = inputQuery.trim();
    setQueryInput('');
    setProcessing(true);

    addMessage({
      sender: 'user',
      text: userText,
    });

    try {
      const updatedState = await agentPlanner.processUserQuery(userText, state, addMessage);
      setState(updatedState);
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Error] ${err.message || 'Failed to process request.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleProvideParameters = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.selectedEndpoint || processing) return;

    setProcessing(true);
    addMessage({
      sender: 'user',
      text: `Provided parameters: ${JSON.stringify(paramInputs)}`,
    });

    try {
      const updatedState: AgentConversationState = {
        ...state,
        extractedParameters: {
          ...state.extractedParameters,
          path_params: { ...state.extractedParameters.path_params, ...paramInputs },
        },
        missingParameters: [],
        step: 'PROPOSED',
      };

      addMessage({
        sender: 'agent',
        text: `[Doc2Action Agent] Parameters received. Creating Human-in-the-Loop Action Proposal...`,
        step: 'PROPOSED',
        decisionType: 'CREATE_PROPOSAL',
      });

      const proposal = await agentTools.createActionProposal({
        endpoint_id: state.selectedEndpoint.id,
        intent_summary: `[Agent Proposal] ${state.intent}`,
        path_params: updatedState.extractedParameters.path_params,
        query_params: updatedState.extractedParameters.query_params,
        body: updatedState.extractedParameters.body,
        ttl_seconds: 300,
      });

      addMessage({
        sender: 'agent',
        text: `[Action Proposal Created] Proposal ID: ${proposal.proposal_id}\nStatus: PENDING CONFIRMATION\nTarget URL: ${proposal.target_url}`,
        step: 'WAITING_FOR_CONFIRMATION',
        proposal: proposal,
        decisionType: 'WAIT_FOR_CONFIRMATION',
      });

      setState({
        ...updatedState,
        step: 'WAITING_FOR_CONFIRMATION',
        activeProposal: proposal,
      });
    } catch (err: any) {
      addMessage({
        sender: 'agent',
        text: `[Proposal Error] ${err.message || 'Failed to create proposal.'}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirmProposal = async (proposalId: string) => {
    setProcessing(true);
    try {
      const confirmedProposal = await agentTools.confirmActionProposal(proposalId);
      addMessage({
        sender: 'agent',
        text: `[Action Proposal Confirmed] Human confirmation registered for Proposal ID ${proposalId}. Ready for execution.`,
        step: 'CONFIRMED',
        proposal: confirmedProposal,
        decisionType: 'WAIT_FOR_CONFIRMATION',
      });
      setState((prev) => ({ ...prev, step: 'CONFIRMED', activeProposal: confirmedProposal }));
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
      const rejectedProposal = await agentTools.rejectActionProposal(proposalId, 'User rejected in Agent workspace');
      addMessage({
        sender: 'agent',
        text: `[Action Proposal Rejected] Proposal ID ${proposalId} has been rejected by user.`,
        step: 'REJECTED',
        proposal: rejectedProposal,
        decisionType: 'INFORMATION',
      });
      setState((prev) => ({ ...prev, step: 'REJECTED', activeProposal: rejectedProposal }));
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

      const execResultProposal: ActionProposalResponse = await agentTools.executeConfirmedAction(proposalId);

      addMessage({
        sender: 'agent',
        text: `[Action Execution Complete] Status: ${execResultProposal.execution_result?.status?.toUpperCase()}\nTarget: ${execResultProposal.target_url}`,
        step: 'COMPLETED',
        proposal: execResultProposal,
        decisionType: 'RESULT',
      });

      setState((prev) => ({
        ...prev,
        step: 'COMPLETED',
        activeProposal: execResultProposal,
      }));
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

  const renderDecisionBadge = (type?: AgentDecisionType) => {
    if (!type) return null;
    const badgeMap: Record<AgentDecisionType, { label: string; color: string }> = {
      INFORMATION: { label: 'Info', color: 'bg-slate-100 text-slate-700 border-slate-200' },
      SEARCH_API: { label: 'RAG Search', color: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
      REQUEST_PARAMETERS: { label: 'Parameters Needed', color: 'bg-amber-100 text-amber-800 border-amber-200' },
      CREATE_PROPOSAL: { label: 'Action Proposed', color: 'bg-sky-100 text-sky-800 border-sky-200' },
      WAIT_FOR_CONFIRMATION: { label: 'Confirmation Required', color: 'bg-amber-100 text-amber-800 border-amber-200' },
      EXECUTE: { label: 'Executing', color: 'bg-blue-100 text-blue-800 border-blue-200' },
      RESULT: { label: 'Execution Result', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
      ERROR: { label: 'Error', color: 'bg-red-100 text-red-800 border-red-200' },
    };

    const b = badgeMap[type] || { label: type, color: 'bg-slate-100 text-slate-700 border-slate-200' };

    return (
      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${b.color}`}>
        {b.label}
      </span>
    );
  };

  const renderStepBadge = (step?: AgentStep) => {
    if (!step || step === 'IDLE') return null;
    const badgeColors: Record<string, string> = {
      SEARCHING: 'bg-sky-100 text-sky-800 border-sky-200',
      PLANNING: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      WAITING_FOR_INPUT: 'bg-amber-100 text-amber-800 border-amber-200',
      WAITING_FOR_CONFIRMATION: 'bg-amber-100 text-amber-800 border-amber-200',
      CONFIRMED: 'bg-sky-100 text-sky-800 border-sky-200',
      EXECUTING: 'bg-blue-100 text-blue-800 border-blue-200',
      COMPLETED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      REJECTED: 'bg-red-100 text-red-800 border-red-200',
      FAILED: 'bg-red-100 text-red-800 border-red-200',
    };

    return (
      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${badgeColors[step] || 'bg-slate-100 text-slate-700'}`}>
        {step}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Agent Workspace</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real Gemini LLM + RAG Knowledge Base + Human-in-the-Loop Action Proposal workflow.
          </p>
        </div>

        {/* Gemini API Key Status Badge */}
        <div className="flex items-center space-x-2">
          {geminiClient.isConfigured() ? (
            <span className="px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-xs font-semibold flex items-center space-x-1.5">
              <Key className="w-3.5 h-3.5 text-emerald-600" />
              <span>Gemini LLM Active</span>
            </span>
          ) : (
            <span className="px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-full text-xs font-semibold flex items-center space-x-1.5">
              <Key className="w-3.5 h-3.5 text-amber-600" />
              <span>Gemini Unconfigured (RAG Fallback)</span>
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Feed */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-[680px]">
          {/* Header */}
          <div className="p-4 bg-slate-900 text-white rounded-t-xl flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center text-white">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold">Doc2Action API Agent</h2>
                <p className="text-[10px] text-slate-400">Gemini LLM + RAG Vector Store + Human Verification</p>
              </div>
            </div>
            {renderStepBadge(state.step)}
          </div>

          {/* Messages Feed */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-2xl p-4 rounded-xl text-xs space-y-3 ${
                    m.sender === 'user'
                      ? 'bg-sky-600 text-white rounded-br-none'
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
                    <div className="p-3 bg-white rounded border border-slate-200 space-y-2 font-mono text-[11px] text-slate-700">
                      <p className="font-bold text-slate-900 flex items-center space-x-1">
                        <Server className="w-3.5 h-3.5 text-indigo-600" />
                        <span>RAG Context Candidates:</span>
                      </p>
                      {m.searchResults.map((hit, idx) => (
                        <div key={idx} className="p-2 bg-slate-50 rounded border border-slate-100 flex items-center justify-between">
                          <span>[{hit.method}] {hit.path}</span>
                          <span className="text-indigo-600 font-bold">{(hit.score * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Action Proposal Card in Message Feed */}
                  {m.proposal && (
                    <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-xl space-y-3 text-slate-900 font-sans">
                      <div className="flex items-center justify-between border-b border-amber-200 pb-2">
                        <span className="font-bold text-amber-900 flex items-center space-x-1">
                          <ShieldCheck className="w-4 h-4 text-amber-600" />
                          <span>Action Proposal #{m.proposal.proposal_id.substring(0, 8)}</span>
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-200 text-amber-900">
                          {m.proposal.status}
                        </span>
                      </div>

                      <div className="text-xs font-mono bg-white p-2.5 rounded border border-amber-100 space-y-1">
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
                              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded flex items-center space-x-1 disabled:opacity-50"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Confirm Proposal</span>
                            </button>
                            <button
                              onClick={() => handleRejectProposal(m.proposal!.proposal_id)}
                              disabled={processing}
                              className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded flex items-center space-x-1 disabled:opacity-50"
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
                            className="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded flex items-center space-x-1 disabled:opacity-50"
                          >
                            <Play className="w-3.5 h-3.5" />
                            <span>Execute Confirmed Action</span>
                          </button>
                        )}
                      </div>

                      {m.proposal.execution_result && (
                        <div className="p-3 bg-emerald-100/60 border border-emerald-200 rounded text-xs font-mono space-y-1">
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
          {state.step === 'WAITING_FOR_INPUT' && state.missingParameters.length > 0 && (
            <div className="p-4 bg-amber-50 border-t border-amber-200 space-y-3">
              <p className="text-xs font-bold text-amber-900 flex items-center space-x-1">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span>Required Parameters Needed:</span>
              </p>

              <form onSubmit={handleProvideParameters} className="space-y-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {state.missingParameters.map((param) => (
                    <div key={param}>
                      <label className="block text-[10px] font-bold text-slate-700 uppercase">{param}</label>
                      <input
                        type="text"
                        required
                        value={paramInputs[param] || ''}
                        onChange={(e) => setParamInputs({ ...paramInputs, [param]: e.target.value })}
                        placeholder={`Enter ${param}`}
                        className="w-full px-2.5 py-1.5 bg-white border border-amber-300 rounded text-xs"
                      />
                    </div>
                  ))}
                </div>
                <button
                  type="submit"
                  disabled={processing}
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded shadow-sm disabled:opacity-50"
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
              placeholder="Tell the agent what to do (e.g. Refund charge ch_123 for $50)..."
              disabled={processing}
              className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white"
            />
            <button
              type="submit"
              disabled={processing || !inputQuery.trim()}
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>
        </div>

        {/* Sidebar Context & State Inspection */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3 flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-sky-600" />
              <span>Agent State Inspection</span>
            </h2>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">Current Step</span>
              <div className="mt-1">{renderStepBadge(state.step)}</div>
            </div>

            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">LLM Provider</span>
              <p className="font-bold text-slate-800 mt-0.5 flex items-center space-x-1">
                <Cpu className="w-3.5 h-3.5 text-indigo-500" />
                <span>{state.llmConfigured ? 'Gemini 1.5 Pro' : 'RAG Fallback Engine'}</span>
              </p>
            </div>

            <div>
              <span className="text-slate-400 font-semibold block uppercase text-[10px]">Intent</span>
              <p className="font-semibold text-slate-900 mt-1 font-sans">{state.intent || 'None'}</p>
            </div>

            {state.selectedEndpoint && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                <span className="text-slate-400 font-semibold block uppercase text-[10px]">Target Endpoint</span>
                <p className="font-bold text-slate-900">[{state.selectedEndpoint.method}] {state.selectedEndpoint.path}</p>
                <p className="text-[10px] text-slate-500 font-sans">{state.selectedEndpoint.summary || state.selectedEndpoint.operation_id}</p>
              </div>
            )}

            {state.activeProposal && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg space-y-1">
                <span className="text-amber-800 font-semibold block uppercase text-[10px]">Active Proposal ID</span>
                <p className="font-bold text-amber-950 truncate">{state.activeProposal.proposal_id}</p>
                <p className="text-[10px] text-amber-700">Expires: {new Date(state.activeProposal.expires_at).toLocaleTimeString()}</p>
              </div>
            )}
          </div>

          <div className="p-4 bg-sky-50/60 border border-sky-100 rounded-lg text-xs space-y-2">
            <p className="font-bold text-sky-900 flex items-center space-x-1">
              <Clock className="w-4 h-4 text-sky-600" />
              <span>Human-in-the-Loop Mandate</span>
            </p>
            <p className="text-slate-600 leading-relaxed font-sans text-[11px]">
              Doc2Action Agent will never execute requests autonomously. Every action requires explicit user confirmation via the Verification subsystem.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
