"""Integration tests for shared storage - database + config together."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from storage.database import OrthoDatabase
from storage.config import OrthoConfig


class TestStorageIntegration:
    """Test database and config working together."""

    @pytest.fixture
    def project_with_config(self):
        """Create a project with config file."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create config
            config_path = tmpdir_path / "config.toml"
            config_content = """
[project]
name = "integration-test"
root = "."
primary_language = "python"

[indexing]
languages = ["python"]
exclude_patterns = []
"""
            config_path.write_text(config_content)

            yield tmpdir_path, config_path

    def test_database_initialization_and_config_load(self, project_with_config):
        """Should be able to init database and load config in same project."""
        project_root, config_path = project_with_config

        # Initialize database
        db = OrthoDatabase(project_root)
        conn = db.connection()
        conn.close()

        # Load config
        config = OrthoConfig.load(config_path)

        assert config.project_name == "integration-test"
        assert (project_root / ".ortho" / "ortho.db").exists()

    def test_multiple_connections_concurrent(self, project_with_config):
        """Should handle multiple concurrent connections."""
        project_root, _ = project_with_config

        db = OrthoDatabase(project_root)

        # Open multiple connections
        conn1 = db.connection()
        conn2 = db.connection()
        conn3 = db.connection()

        # All should work
        for conn in [conn1, conn2, conn3]:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

        for conn in [conn1, conn2, conn3]:
            conn.close()

    def test_database_persistence_across_connections(self, project_with_config):
        """Data written in one connection should be readable in another."""
        project_root, _ = project_with_config

        db = OrthoDatabase(project_root)

        # Create table in first connection
        conn1 = db.connection()
        cursor1 = conn1.cursor()
        cursor1.execute("""
            CREATE TABLE symbols (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                module TEXT NOT NULL
            )
        """)
        cursor1.execute("INSERT INTO symbols (name, module) VALUES ('func1', 'module1')")
        conn1.commit()
        conn1.close()

        # Read in second connection
        conn2 = db.connection()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT name, module FROM symbols")
        result = cursor2.fetchone()

        assert result == ("func1", "module1")
        conn2.close()

    def test_foreign_key_constraint_enabled(self, project_with_config):
        """Foreign key constraints should be enforced."""
        project_root, _ = project_with_config

        db = OrthoDatabase(project_root)
        conn = db.connection()
        cursor = conn.cursor()

        # Create parent table
        cursor.execute("""
            CREATE TABLE modules (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        # Create child table with FK
        cursor.execute("""
            CREATE TABLE symbols (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                module_id INTEGER NOT NULL,
                FOREIGN KEY (module_id) REFERENCES modules (id)
            )
        """)
        conn.commit()

        # Try to insert invalid FK (should fail)
        with pytest.raises(Exception):  # sqlite3.IntegrityError
            cursor.execute("INSERT INTO symbols (name, module_id) VALUES ('func', 999)")
            conn.commit()

        conn.close()

    def test_wal_mode_persistence(self, project_with_config):
        """WAL mode should persist across connections."""
        project_root, _ = project_with_config

        db = OrthoDatabase(project_root)

        # Check in first connection
        conn1 = db.connection()
        cursor1 = conn1.cursor()
        cursor1.execute("PRAGMA journal_mode")
        mode1 = cursor1.fetchone()[0]
        conn1.close()

        # Check in second connection
        conn2 = db.connection()
        cursor2 = conn2.cursor()
        cursor2.execute("PRAGMA journal_mode")
        mode2 = cursor2.fetchone()[0]
        conn2.close()

        assert mode1 == "wal"
        assert mode2 == "wal"

    def test_config_path_and_db_path_independent(self, project_with_config):
        """Config and database paths should be independent."""
        project_root, config_path = project_with_config

        db = OrthoDatabase(project_root)
        config = OrthoConfig.load(config_path)

        # Different locations
        assert db.db_path != config_path
        assert str(db.db_path).endswith("ortho.db")
        assert str(config_path).endswith("config.toml")
