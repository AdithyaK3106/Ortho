import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class OrthoDatabase:
    """Single SQLite connection manager for the .ortho/ directory."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".ortho" / "ortho.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def migrate(self) -> None:
        """Run all pending migrations in order, each exactly once.

        A schema_migrations ledger records applied files: executescript cannot
        branch, so rebuild-style migrations (002+) must not replay (ADR-012).
        Pre-ledger databases replay 001 harmlessly (IF NOT EXISTS throughout)
        and are then tracked.
        """
        migrations_dir = Path(__file__).parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))

        conn = self.connection()
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )

        for migration_file in migration_files:
            applied = cursor.execute(
                "SELECT 1 FROM schema_migrations WHERE filename = ?",
                (migration_file.name,),
            ).fetchone()
            if applied:
                continue
            with open(migration_file, "r") as f:
                sql = f.read()
            cursor.executescript(sql)
            cursor.execute(
                "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)",
                (migration_file.name, datetime.now(timezone.utc).isoformat()),
            )

        conn.commit()
        conn.close()

    def connection(self) -> sqlite3.Connection:
        """Returns a connection with WAL mode and foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
