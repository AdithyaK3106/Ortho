"""Pytest configuration and fixtures for arch-intelligence tests."""

import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from database import OrthoDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        db = OrthoDatabase(project_root)
        db.migrate()
        yield db


@pytest.fixture
def sample_repo_id():
    """Sample repository ID for testing."""
    return "test-repo-001"


@pytest.fixture
def mock_symbol_repo(temp_db, sample_repo_id):
    """Create a mock symbol repository."""
    conn = temp_db.connection()

    # Insert repository
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (sample_repo_id, "/test/repo", "test-repo"),
    )

    # Insert files
    files = [
        ("file-1", "presentation/handlers.py", "python"),
        ("file-2", "presentation/views.py", "python"),
        ("file-3", "presentation/serializers.py", "python"),
        ("file-4", "business/auth.py", "python"),
        ("file-5", "business/user.py", "python"),
        ("file-6", "business/order.py", "python"),
        ("file-7", "business/payment.py", "python"),
        ("file-8", "data/user_repo.py", "python"),
        ("file-9", "data/order_repo.py", "python"),
        ("file-10", "data/payment_repo.py", "python"),
        ("file-11", "utils/logger.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            """INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified)
               VALUES (?, ?, ?, ?, ?, datetime('now'))""",
            (file_id, sample_repo_id, rel_path, lang, 100),
        )

    # Insert import edges (layered structure: presentation → business → data)
    edges = [
        # Presentation → Business
        ("file-1", "file-4"),  # handlers → auth
        ("file-1", "file-5"),  # handlers → user
        ("file-2", "file-5"),  # views → user
        ("file-3", "file-5"),  # serializers → user
        # Business → Data
        ("file-4", "file-8"),  # auth → user_repo
        ("file-5", "file-8"),  # user → user_repo
        ("file-5", "file-9"),  # user → order_repo
        ("file-6", "file-9"),  # order → order_repo
        ("file-7", "file-10"), # payment → payment_repo
        # Utils (independent)
        ("file-4", "file-11"), # auth → logger
    ]

    for importer, imported in edges:
        conn.execute(
            """INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external)
               VALUES (?, ?, ?, 0)""",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()

    return temp_db
