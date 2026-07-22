-- 003: git_history table (task-025 part 1)
-- GitMetadataStore (context-hub) was built against this shape but no
-- migration in the live .ortho/ortho.db path ever created it, so the table
-- never existed outside context-hub's own in-memory test schema
-- (init_git_history_schema in context_hub/schema.py). Ortho scan now calls
-- GitMetadataStore.load_git_history() per file; this migration makes that
-- write target actually exist.

-- UNIQUE(file_id, commit_hash) is required, not decorative: load_git_history
-- uses INSERT OR IGNORE to make rescans idempotent, which is a silent no-op
-- without a matching unique constraint -- every rescan would otherwise
-- duplicate every row for every file, unbounded, on every `ortho scan`.
CREATE TABLE IF NOT EXISTS git_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL,
    repo_id TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    author TEXT,
    commit_date TEXT NOT NULL,
    message TEXT,
    diff_lines_added INTEGER,
    diff_lines_removed INTEGER,
    UNIQUE(file_id, commit_hash)
);

CREATE INDEX IF NOT EXISTS idx_git_history_file ON git_history(file_id);
CREATE INDEX IF NOT EXISTS idx_git_history_commit ON git_history(commit_hash);
