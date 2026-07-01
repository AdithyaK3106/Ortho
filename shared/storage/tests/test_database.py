"""Tests for OrthoDatabase - SQLite connection management."""

import pytest
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from storage.database import OrthoDatabase


class TestOrthoDatabase:
    """Test OrthoDatabase connection and migration."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_database_initialization(self, temp_project):
        """Database should create .ortho directory and db file."""
        db = OrthoDatabase(temp_project)
        assert db.project_root == temp_project
        assert db.db_path == temp_project / ".ortho" / "ortho.db"

    def test_connection_creates_database_file(self, temp_project):
        """Connection should auto-create database file."""
        db = OrthoDatabase(temp_project)
        assert not db.db_path.exists()

        conn = db.connection()
        conn.close()

        assert db.db_path.exists()

    def test_connection_returns_sqlite_connection(self, temp_project):
        """Connection should return valid SQLite connection."""
        db = OrthoDatabase(temp_project)
        conn = db.connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_connection_has_wal_mode(self, temp_project):
        """Connection should enable WAL mode for concurrent access."""
        db = OrthoDatabase(temp_project)
        conn = db.connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        assert mode == "wal"
        conn.close()

    def test_connection_has_foreign_keys_enabled(self, temp_project):
        """Connection should enable foreign key constraints."""
        db = OrthoDatabase(temp_project)
        conn = db.connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]

        assert enabled == 1
        conn.close()

    def test_multiple_connections(self, temp_project):
        """Should be able to open multiple connections."""
        db = OrthoDatabase(temp_project)
        conn1 = db.connection()
        conn2 = db.connection()

        assert conn1 is not conn2
        conn1.close()
        conn2.close()

    def test_db_path_different_for_different_projects(self):
        """Different projects should have different db paths."""
        with TemporaryDirectory() as tmpdir1, TemporaryDirectory() as tmpdir2:
            db1 = OrthoDatabase(tmpdir1)
            db2 = OrthoDatabase(tmpdir2)

            assert db1.db_path != db2.db_path

    def test_connection_can_execute_query(self, temp_project):
        """Should be able to execute queries on connection."""
        db = OrthoDatabase(temp_project)
        conn = db.connection()
        cursor = conn.cursor()

        # Simple query to test connection works
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        assert result[0] == 1
        conn.close()

    def test_multiple_connections_share_same_db_file(self, temp_project):
        """Multiple connections should access same database file."""
        db = OrthoDatabase(temp_project)

        conn1 = db.connection()
        cursor1 = conn1.cursor()
        cursor1.execute("CREATE TABLE test (id INTEGER)")
        conn1.commit()
        conn1.close()

        # Second connection should see the table
        conn2 = db.connection()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test'")
        result = cursor2.fetchone()

        assert result is not None
        conn2.close()
