-- Ortho v3 Initial Schema (FRD Section 14)

-- Core repository
CREATE TABLE IF NOT EXISTS repositories (
    id TEXT PRIMARY KEY,
    root_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    primary_language TEXT,
    indexed_at TEXT,
    git_remote TEXT,
    config_json TEXT
);

-- File manifest
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    rel_path TEXT NOT NULL,
    language TEXT NOT NULL,
    size_bytes INTEGER,
    last_modified TEXT,
    git_last_commit TEXT,
    UNIQUE(repo_id, rel_path)
);
CREATE INDEX IF NOT EXISTS idx_files_repo ON files(repo_id);

-- Symbol registry
CREATE TABLE IF NOT EXISTS symbols (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    file_id TEXT NOT NULL REFERENCES files(id),
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('function','class','method','variable','constant','type')),
    visibility TEXT NOT NULL CHECK(visibility IN ('public','private','protected','internal')),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    docstring TEXT,
    signature TEXT
);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_symbols_qualified ON symbols(qualified_name);

-- Call graph
CREATE TABLE IF NOT EXISTS call_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_id TEXT NOT NULL REFERENCES symbols(id),
    callee_id TEXT NOT NULL REFERENCES symbols(id),
    call_site_line INTEGER,
    confidence REAL NOT NULL DEFAULT 0.8
);
CREATE INDEX IF NOT EXISTS idx_call_edges_caller ON call_edges(caller_id);
CREATE INDEX IF NOT EXISTS idx_call_edges_callee ON call_edges(callee_id);

-- Import graph
CREATE TABLE IF NOT EXISTS import_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    importer_file_id TEXT NOT NULL REFERENCES files(id),
    imported_file_id TEXT REFERENCES files(id),
    imported_module TEXT NOT NULL,
    is_external INTEGER NOT NULL DEFAULT 0,
    symbols_imported TEXT
);

-- ContextHub artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_modified TEXT NOT NULL,
    relevance_scope TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    related_symbols TEXT DEFAULT '[]',
    estimated_tokens INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);

-- FTS5 full-text search on artifacts
CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
    title,
    content,
    content='artifacts',
    content_rowid='id'
);

-- Project memory
CREATE TABLE IF NOT EXISTS project_memory (
    key TEXT NOT NULL,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    value TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (key, repo_id)
);

-- Architecture model
CREATE TABLE IF NOT EXISTS architecture_models (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    style TEXT NOT NULL,
    style_confidence REAL NOT NULL,
    evidence TEXT NOT NULL,
    model_json TEXT NOT NULL,
    detected_at TEXT NOT NULL
);

-- Workflow runs
CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    intent TEXT NOT NULL,
    intent_class TEXT NOT NULL,
    execution_plan_json TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    evidence_json TEXT NOT NULL DEFAULT '[]'
);

-- Agent/skill registry cache
CREATE TABLE IF NOT EXISTS agent_manifests (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    loaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_manifests (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    content TEXT NOT NULL,
    estimated_tokens INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    loaded_at TEXT NOT NULL
);
