export interface ContextChunk {
  id: string;
  source_type: "symbol" | "artifact" | "git" | "architecture";
  source_id: string;
  content: string;
  relevance_score: number;
  token_count: number;
  included: boolean;
}

export interface TokenBudget {
  total: number;
  used: number;
  model: string;
}

export interface TokenBudgetStatus extends TokenBudget {
  remaining: number;
}

export interface ContextPackage {
  id: string;
  workflow_run_id: string;
  step_id: string;
  chunks: ContextChunk[];
  budget: TokenBudgetStatus;
  assembled_at: Date;
}
