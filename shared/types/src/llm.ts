export interface LLMRequest {
  model: string;
  system_prompt: string;
  context_package_id: string;
  user_message: string;
  max_tokens: number;
  temperature: number;
}

export interface LLMResponse {
  model: string;
  content: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  stop_reason: string;
}
