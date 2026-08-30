import { agentConfig } from './config';
import type { StructuredAgentDecision } from './types';

export const SYSTEM_INSTRUCTION = `
You are Doc2Action, an API action assistant.
You help users operate registered APIs in their catalog.
MANDATORY RULES:
1. You MUST select endpoints strictly from the provided RAG context or catalog.
2. You MUST NOT invent endpoints or execute arbitrary URLs.
3. You MUST NOT execute actions without explicit human confirmation.
4. When required parameters are missing, output type "REQUEST_PARAMETERS" with "missing_params".
5. Output structured JSON matching:
{
  "type": "INFORMATION" | "SEARCH_API" | "REQUEST_PARAMETERS" | "CREATE_PROPOSAL" | "ERROR",
  "explanation": "Human-readable reasoning",
  "intent_summary": "Short action summary",
  "extracted_params": {
    "path_params": {},
    "query_params": {},
    "body": {}
  },
  "missing_params": []
}
`.trim();

export class GeminiLLMClient {
  private get apiKey(): string {
    return (import.meta.env.VITE_GEMINI_API_KEY || agentConfig.geminiApiKey || '').trim();
  }

  public isConfigured(): boolean {
    return this.apiKey.length > 0;
  }

  public async evaluateIntentAndContext(
    prompt: string,
    ragContext?: string
  ): Promise<StructuredAgentDecision> {
    if (!this.isConfigured()) {
      return {
        type: 'INFORMATION',
        explanation: 'Gemini is not configured. Set VITE_GEMINI_API_KEY in your environment to enable live LLM reasoning.',
      };
    }

    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${agentConfig.modelName}:generateContent?key=${this.apiKey}`;
      const payload = {
        contents: [
          {
            parts: [
              {
                text: `${SYSTEM_INSTRUCTION}\n\nRAG Context:\n${ragContext || 'None'}\n\nUser Prompt: ${prompt}`,
              },
            ],
          },
        ],
        generationConfig: {
          responseMimeType: 'application/json',
        },
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Gemini HTTP error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!text) {
        throw new Error('Empty text payload returned by Gemini API');
      }

      const parsed: StructuredAgentDecision = JSON.parse(text);
      return parsed;
    } catch (err: any) {
      return {
        type: 'ERROR',
        explanation: `Gemini Reasoning Error: ${err.message || 'Failed to parse Gemini response'}`,
      };
    }
  }
}

export const geminiClient = new GeminiLLMClient();
