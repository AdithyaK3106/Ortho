-- Migration: Add architecture_models table (task-005)

CREATE TABLE IF NOT EXISTS architecture_models (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    style TEXT NOT NULL,
    style_confidence REAL NOT NULL,
    evidence TEXT NOT NULL DEFAULT '[]',  -- JSON array
    model_json TEXT NOT NULL,              -- Full ArchitectureModel as JSON
    detected_at TEXT NOT NULL,
    UNIQUE(repo_id, detected_at)
);

CREATE INDEX IF NOT EXISTS idx_arch_models_repo_date
ON architecture_models(repo_id, detected_at DESC);
