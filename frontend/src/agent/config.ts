export const agentConfig = {
  geminiApiKey: import.meta.env.VITE_GEMINI_API_KEY || '',
  modelName: 'gemini-1.5-pro',
  defaultTopK: 5,
  proposalTTLSeconds: 300,
};
