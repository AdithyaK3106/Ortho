-- 002: Canonical artifacts schema (ADR-012)
-- Reconciles migration 001's artifacts shape with context-hub schema.py:
-- adds version column with PRIMARY KEY (id, version), rebuilds FTS5 on rowid,
-- adds the three sync triggers. Runs exactly once via the schema_migrations
-- ledger in OrthoDatabase.migrate(); artifacts_old is retained as the
-- rollback backup per rollback-plan.md (dropped in a future migration).

ALTER TABLE artifacts RENAME TO artifacts_old;

CREATE TABLE artifacts (
    id TEXT NOT NULL,
    version INTEGER NOT NULL,
    repo_id TEXT NOT NULL,
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
    content_hash TEXT NOT NULL,
    PRIMARY KEY (id, version)
);

INSERT INTO artifacts
    (id, version, repo_id, type, title, content, source, created_at, last_modified,
     relevance_scope, tags, related_symbols, estimated_tokens, content_hash)
SELECT
    id, 1, repo_id, type, title, content, source, created_at, last_modified,
    relevance_scope, tags, related_symbols, estimated_tokens, content_hash
FROM artifacts_old;

CREATE INDEX IF NOT EXISTS idx_artifacts_repo ON artifacts(repo_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);
CREATE INDEX IF NOT EXISTS idx_artifacts_scope ON artifacts(relevance_scope);
CREATE INDEX IF NOT EXISTS idx_artifacts_created ON artifacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_artifacts_source ON artifacts(source);

-- Migration 001's FTS5 declared content_rowid='id' (TEXT — invalid for external
-- content tables). Rebuild on the integer rowid and repopulate.
DROP TABLE IF EXISTS artifacts_fts;

CREATE VIRTUAL TABLE artifacts_fts USING fts5(
    title,
    content,
    content='artifacts',
    content_rowid='rowid'
);

INSERT INTO artifacts_fts (rowid, title, content)
SELECT rowid, title, content FROM artifacts;

CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, content)
    VALUES (NEW.rowid, NEW.title, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
    INSERT INTO artifacts_fts(rowid, title, content)
    VALUES (NEW.rowid, NEW.title, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
END;
