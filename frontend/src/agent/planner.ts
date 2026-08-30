import { agentTools } from './tools';
import { geminiClient } from './client';
import type { ChatMessage, AgentConversationState } from './types';
import type { RAGSearchResult } from '../types/api';

export class AgentPlanner {
  public static createInitialState(): AgentConversationState {
    return {
      step: 'IDLE',
      intent: '',
      selectedConnection: null,
      selectedEndpoint: null,
      extractedParameters: {
        path_params: {},
        query_params: {},
        body: {},
      },
      missingParameters: [],
      activeProposal: null,
      executionResult: null,
      error: null,
      llmConfigured: geminiClient.isConfigured(),
    };
  }

  /**
   * Controlled Multi-turn Agent Planning Flow:
   * 1. Check Gemini LLM configuration.
   * 2. RAG Search over catalog embeddings.
   * 3. Validate candidate endpoint against catalog.
   * 4. LLM reasoning or parameter extraction.
   * 5. Detect missing required parameters.
   * 6. Generate Action Proposal via backend verification service.
   */
  public async processUserQuery(
    userQuery: string,
    existingState: AgentConversationState,
    addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  ): Promise<AgentConversationState> {
    const isConfigured = geminiClient.isConfigured();
    const newState: AgentConversationState = {
      ...existingState,
      intent: userQuery,
      step: 'SEARCHING',
      llmConfigured: isConfigured,
    };

    if (!isConfigured) {
      addMessage({
        sender: 'agent',
        text: `[System Warning] Gemini API Key is not configured (VITE_GEMINI_API_KEY). Proceeding with RAG Knowledge Base and deterministic parameter engine.`,
        step: 'SEARCHING',
        decisionType: 'INFORMATION',
      });
    }

    addMessage({
      sender: 'agent',
      text: `[Doc2Action Agent] Searching RAG Knowledge Base for catalog endpoints matching "${userQuery}"...`,
      step: 'SEARCHING',
      decisionType: 'SEARCH_API',
    });

    try {
      // Step 1: Semantic Search in RAG Knowledge Base
      const searchResults: RAGSearchResult[] = await agentTools.searchApiCatalog(userQuery);

      if (!searchResults || searchResults.length === 0) {
        addMessage({
          sender: 'agent',
          text: `[Doc2Action Agent] No matching catalog endpoints found for your request. Please ensure an API connection is registered and indexed in the API Catalog.`,
          step: 'FAILED',
          decisionType: 'ERROR',
        });
        return { ...newState, step: 'FAILED', error: 'No matching catalog endpoints found.' };
      }

      const topHit = searchResults[0];
      addMessage({
        sender: 'agent',
        text: `Found endpoint hit: [${topHit.method}] ${topHit.path} (${topHit.connection_name}) with ${(topHit.score * 100).toFixed(1)}% similarity match.`,
        step: 'PLANNING',
        searchResults: searchResults,
        decisionType: 'SEARCH_API',
      });

      // Step 2: Validate against user's registered catalog endpoints
      const connectionId = topHit.connection_id;
      const endpointId = topHit.endpoint_id;

      if (!connectionId || !endpointId) {
        throw new Error('Top RAG search result is missing valid catalog connection or endpoint identifier.');
      }

      const endpoints = await agentTools.getConnectionEndpoints(connectionId);
      const targetEndpoint = endpoints.find((ep) => ep.id === endpointId) || null;

      if (!targetEndpoint) {
        throw new Error('Target endpoint suggested by RAG does not exist in user catalog.');
      }

      // Step 3: LLM Intent & Decision Evaluation
      const decision = await geminiClient.evaluateIntentAndContext(userQuery, topHit.content);

      if (decision.type === 'ERROR') {
        addMessage({
          sender: 'agent',
          text: `[LLM Error] ${decision.explanation}`,
          step: 'FAILED',
          decisionType: 'ERROR',
        });
        return { ...newState, step: 'FAILED', error: decision.explanation };
      }

      // Step 4: Analyze missing required path parameters
      const declaredParams = targetEndpoint.parameters || [];
      const requiredPathParams = declaredParams
        .filter((p: any) => p.in === 'path' && p.required)
        .map((p: any) => p.name);

      const missingParams: string[] = [];
      for (const reqParam of requiredPathParams) {
        if (!newState.extractedParameters.path_params[reqParam]) {
          missingParams.push(reqParam);
        }
      }

      if (missingParams.length > 0) {
        addMessage({
          sender: 'agent',
          text: `${decision.explanation}\n\nTo prepare the action proposal for [${targetEndpoint.method}] ${targetEndpoint.path}, please provide the required parameters: ${missingParams.join(', ')}.`,
          step: 'WAITING_FOR_INPUT',
          selectedEndpoint: targetEndpoint,
          requiredParameters: missingParams,
          decisionType: 'REQUEST_PARAMETERS',
        });

        return {
          ...newState,
          step: 'WAITING_FOR_INPUT',
          selectedEndpoint: targetEndpoint,
          missingParameters: missingParams,
        };
      }

      // Step 5: Create Action Proposal via backend verification service
      addMessage({
        sender: 'agent',
        text: `[Doc2Action Agent] Creating Human-in-the-Loop Action Proposal for [${targetEndpoint.method}] ${targetEndpoint.path}...`,
        step: 'PROPOSED',
        selectedEndpoint: targetEndpoint,
        decisionType: 'CREATE_PROPOSAL',
      });

      const proposal = await agentTools.createActionProposal({
        endpoint_id: targetEndpoint.id,
        intent_summary: decision.intent_summary || `[Agent Proposal] ${userQuery}`,
        path_params: newState.extractedParameters.path_params,
        query_params: newState.extractedParameters.query_params,
        body: newState.extractedParameters.body,
        ttl_seconds: 300,
      });

      addMessage({
        sender: 'agent',
        text: `[Action Proposal Created] Proposal ID: ${proposal.proposal_id}\nStatus: PENDING CONFIRMATION\nTarget URL: ${proposal.target_url}\n\nExplicit human confirmation is required prior to execution.`,
        step: 'WAITING_FOR_CONFIRMATION',
        proposal: proposal,
        decisionType: 'WAIT_FOR_CONFIRMATION',
      });

      return {
        ...newState,
        step: 'WAITING_FOR_CONFIRMATION',
        selectedEndpoint: targetEndpoint,
        activeProposal: proposal,
      };

    } catch (err: any) {
      const errorMsg = err.message || 'An error occurred during agent planning.';
      addMessage({
        sender: 'agent',
        text: `[Doc2Action Agent Error] ${errorMsg}`,
        step: 'FAILED',
        decisionType: 'ERROR',
      });
      return { ...newState, step: 'FAILED', error: errorMsg };
    }
  }
}

export const agentPlanner = new AgentPlanner();
