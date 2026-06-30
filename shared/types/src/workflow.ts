export interface WorkflowRun {
  id: string;
  repo_id: string;
  intent: string;
  intent_class: string;
  execution_plan: ExecutionPlan;
  status: "pending" | "running" | "awaiting_approval" | "approved" | "rejected" | "complete" | "failed";
  started_at: Date;
  completed_at?: Date;
  evidence: Evidence[];
}

export interface ExecutionPlan {
  intent_class: string;
  steps: ExecutionStep[];
  total_estimated_tokens: number;
  human_approval_required: boolean;
  approval_reason?: string;
}

export interface ExecutionStep {
  step_id: string;
  agent_name: string;
  skill_names: string[];
  context_package_id: string;
  receives_from?: string;
  produces: string;
  approval_gate: boolean;
  status: "pending" | "running" | "complete" | "failed";
}

export interface Evidence {
  type: "test_output" | "lint_result" | "coverage" | "review_note" | "approval";
  content: string;
  produced_at: Date;
  step_id: string;
}
