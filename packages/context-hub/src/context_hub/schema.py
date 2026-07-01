"""Schema initialization and migrations for ContextHub."""

import sqlite3
from pathlib import Path


def init_artifact_schema(db: sqlite3.Connection) -> None:
    """Create artifacts table, FTS5 virtual table, and automatic sync triggers."""

    # Main artifacts table
    db.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
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
            version INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Indexes for common queries
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_artifacts_repo ON artifacts(repo_id)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_artifacts_scope ON artifacts(relevance_scope)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_artifacts_created ON artifacts(created_at DESC)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_artifacts_source ON artifacts(source)
    """)

    # FTS5 virtual table for BM25 search
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
            title,
            content,
            content='artifacts',
            content_rowid='rowid'
        )
    """)

    # Automatic synchronization triggers
    db.execute("""
        CREATE TRIGGER IF NOT EXISTS artifacts_ai AFTER INSERT ON artifacts BEGIN
            INSERT INTO artifacts_fts(rowid, title, content)
            VALUES (NEW.rowid, NEW.title, NEW.content);
        END
    """)

    db.execute("""
        CREATE TRIGGER IF NOT EXISTS artifacts_au AFTER UPDATE ON artifacts BEGIN
            DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
            INSERT INTO artifacts_fts(rowid, title, content)
            VALUES (NEW.rowid, NEW.title, NEW.content);
        END
    """)

    db.execute("""
        CREATE TRIGGER IF NOT EXISTS artifacts_ad AFTER DELETE ON artifacts BEGIN
            DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
        END
    """)

    db.commit()


def init_git_history_schema(db: sqlite3.Connection) -> None:
    """Create git_history table for file churn tracking."""

    db.execute("""
        CREATE TABLE IF NOT EXISTS git_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            repo_id TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            author TEXT,
            commit_date TEXT NOT NULL,
            message TEXT,
            diff_lines_added INTEGER,
            diff_lines_removed INTEGER
        )
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_git_history_file ON git_history(file_id)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_git_history_commit ON git_history(commit_hash)
    """)

    db.commit()


def init_project_memory_schema(db: sqlite3.Connection) -> None:
    """Create project_memory table for key/value project facts."""

    db.execute("""
        CREATE TABLE IF NOT EXISTS project_memory (
            key TEXT NOT NULL,
            repo_id TEXT NOT NULL,
            value TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'manual',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (key, repo_id)
        )
    """)

    db.commit()


def init_artifact_embeddings_schema(db: sqlite3.Connection) -> None:
    """Create artifact_embeddings virtual table for semantic search."""
    try:
        import sqlite_vec

        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)

        db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS artifact_embeddings USING vec0(
                artifact_id TEXT PRIMARY KEY,
                embedding FLOAT[1536]
            )
        """)

        db.commit()
    except (ImportError, sqlite3.OperationalError):
        # sqlite-vec not available or not installed
        # Graceful degradation: semantic search will be unavailable
        pass


def init_all_schemas(db: sqlite3.Connection) -> None:
    """Initialize all ContextHub schemas."""
    init_artifact_schema(db)
    init_git_history_schema(db)
    init_project_memory_schema(db)
    init_artifact_embeddings_schema(db)
