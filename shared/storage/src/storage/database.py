import sqlite3
from pathlib import Path
from typing import Optional


class OrthoDatabase:
    """Single SQLite connection manager for the .ortho/ directory."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".ortho" / "ortho.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def migrate(self) -> None:
        """Run all pending migrations in order."""
        migrations_dir = Path(__file__).parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))

        conn = self.connection()
        cursor = conn.cursor()

        for migration_file in migration_files:
            with open(migration_file, "r") as f:
                sql = f.read()
            cursor.executescript(sql)

        conn.commit()
        conn.close()

    def connection(self) -> sqlite3.Connection:
        """Returns a connection with WAL mode and foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
