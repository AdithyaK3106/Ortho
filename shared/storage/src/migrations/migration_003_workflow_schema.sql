-- Migration 003: Workflow Schema
-- Tracks execution plans, workflow runs, and orchestration state
-- Append-only: new tables only, no changes to existing schema
-- Date: 2026-07-07

CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    intent TEXT NOT NULL,
    intent_class TEXT NOT NULL,
    execution_plan_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','running','awaiting_approval','rejected','complete','failed')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL DEFAULT 'orchestration'
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_repo ON workflow_runs(repo_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_started ON workflow_runs(started_at DESC);

CREATE TABLE IF NOT EXISTS execution_steps (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    skill_names TEXT NOT NULL,
    approval_gate INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('pending','pending_approval','running','complete','failed','rejected')),
    result_json TEXT,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_execution_steps_workflow ON execution_steps(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_execution_steps_status ON execution_steps(status);
CREATE INDEX IF NOT EXISTS idx_execution_steps_step_id ON execution_steps(step_id);

CREATE TABLE IF NOT EXISTS approval_gates (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','timeout')),
    decision_reason TEXT,
    created_at TEXT NOT NULL,
    decided_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_approval_gates_workflow ON approval_gates(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_approval_gates_step ON approval_gates(step_id);

-- Record migration
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (3, 'Workflow schema: workflow_runs, execution_steps, approval_gates', datetime('now', 'utc'));
