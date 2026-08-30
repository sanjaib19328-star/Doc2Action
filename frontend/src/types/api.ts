// User & Auth Types
export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface UserRegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

// OpenAPI Discovery Types
export interface DiscoverSpecRequest {
  url: string;
}

export interface APIOperation {
  id: string;
  operation_id?: string | null;
  path: string;
  method: string;
  summary?: string | null;
  description?: string | null;
  parameters: any[];
  request_body?: Record<string, any> | null;
  responses: Record<string, any>;
  security: any[];
}

export interface APISecurityScheme {
  id: string;
  scheme_name: string;
  type: string;
  scheme_in?: string | null;
  name?: string | null;
  scheme?: string | null;
  bearer_format?: string | null;
  details: Record<string, any>;
}

export interface APISpecification {
  id: string;
  owner_id: string;
  title: string;
  description?: string | null;
  version: string;
  spec_version: string;
  source_url: string;
  base_url?: string | null;
  servers: any[];
  created_at: string;
  updated_at: string;
}

export interface APISpecificationDetail extends APISpecification {
  operations: APIOperation[];
  security_schemes: APISecurityScheme[];
}

// API Catalog Types
export interface APIConnectionCreate {
  specification_id: string;
  name?: string;
  base_url?: string;
  auth_config?: Record<string, any>;
}

export interface APIEndpoint {
  id: string;
  connection_id: string;
  operation_id?: string | null;
  method: string;
  path: string;
  summary?: string | null;
  description?: string | null;
  parameters: any[];
  request_body_schema?: Record<string, any> | null;
  response_schema: Record<string, any>;
  security_requirements: any[];
  created_at: string;
  updated_at: string;
}

export interface APIConnection {
  id: string;
  owner_id: string;
  specification_id: string;
  name: string;
  base_url: string;
  is_active: boolean;
  auth_config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface APIConnectionDetail extends APIConnection {
  endpoints: APIEndpoint[];
}

// RAG Types
export interface RAGSearchRequest {
  query: string;
  connection_id?: string;
  top_k?: number;
}

export interface RAGSearchResult {
  endpoint_id?: string | null;
  connection_id?: string | null;
  connection_name?: string | null;
  method?: string | null;
  path?: string | null;
  operation_id?: string | null;
  base_url?: string | null;
  score: number;
  content: string;
}

export interface RAGIndexResponse {
  message: string;
  connection_id: string;
  indexed_count: number;
}

export interface RAGDeleteResponse {
  message: string;
  connection_id: string;
  deleted_count: number;
}

// Execution Types
export interface ExecutionPreviewRequest {
  endpoint_id: string;
  path_params?: Record<string, any>;
  query_params?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
}

export interface ExecutionPreviewResponse {
  endpoint_id: string;
  connection_name: string;
  method: string;
  target_url: string;
  masked_headers: Record<string, string>;
  query_params: Record<string, any>;
  body?: any;
  security_type?: string | null;
}

export interface ExecutionExecuteRequest extends ExecutionPreviewRequest {
  confirmed: boolean;
}

export interface ExecutionResponse {
  execution_id: string;
  connection_id: string;
  endpoint_id: string;
  method: string;
  target_url: string;
  status_code?: number | null;
  status: 'success' | 'error' | 'timeout' | 'failed';
  latency_ms: number;
  request_headers: Record<string, string>;
  request_params: Record<string, any>;
  request_body?: any;
  response_body?: any;
  error_message?: string | null;
  created_at: string;
}

// Human-in-the-loop Verification Types
export interface CreateActionProposalRequest {
  endpoint_id: string;
  intent_summary: string;
  path_params?: Record<string, any>;
  query_params?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
  ttl_seconds?: number;
}

export interface ActionProposalResponse {
  proposal_id: string;
  user_id: string;
  connection_id: string;
  endpoint_id: string;
  intent_summary: string;
  http_method: string;
  target_url: string;
  path_params: Record<string, any>;
  query_params: Record<string, any>;
  headers: Record<string, string>;
  body?: any;
  status: 'pending' | 'confirmed' | 'rejected' | 'executed' | 'expired';
  expires_at: string;
  execution_result?: Record<string, any> | null;
  created_at: string;
}

export interface RejectProposalRequest {
  reason?: string;
}

// Generic API Error Format
export interface APIErrorResponse {
  error: {
    message: string;
    details?: any;
    type?: string;
  };
}
