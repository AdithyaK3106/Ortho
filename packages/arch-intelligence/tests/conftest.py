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
        # CRITICAL: Explicitly close all connections before cleanup
        # On Windows, SQLite locks persist if connections aren't closed,
        # preventing tempfile cleanup
        try:
            # Close all open connections from the pool
            db.close()
        except Exception:
            pass


@pytest.fixture
def sample_repo_id():
    """Sample repository ID for testing."""
    return "test-repo-001"


@pytest.fixture
def mock_symbol_repo(temp_db, sample_repo_id):
    """Create a mock symbol repository with layered structure."""
    conn = temp_db.connection()

    # Insert repository
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (sample_repo_id, "/test/repo", "test-repo"),
    )

    # Insert files for layered architecture
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


# ============================================================================
# Architecture Pattern Fixtures (for pattern detection tests)
# ============================================================================


@pytest.fixture
def layered_repo_id():
    """ID for layered fixture."""
    return "layered-repo"


@pytest.fixture
def layered_fixture_db(temp_db, layered_repo_id):
    """Canonical layered architecture fixture."""
    conn = temp_db.connection()
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (layered_repo_id, "/fixtures/layered", "layered-arch"),
    )

    # Layered: 3 tiers (presentation → business → data)
    files = [
        ("l1", "presentation/handlers.py", "python"),
        ("l2", "presentation/views.py", "python"),
        ("l3", "presentation/serializers.py", "python"),
        ("l4", "business/auth.py", "python"),
        ("l5", "business/user.py", "python"),
        ("l6", "business/order.py", "python"),
        ("l7", "business/payment.py", "python"),
        ("l8", "data/user_repo.py", "python"),
        ("l9", "data/order_repo.py", "python"),
        ("l10", "data/payment_repo.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (file_id, layered_repo_id, rel_path, lang, 100),
        )

    # STRICT layering: presentation → business → data (no back edges)
    edges = [
        ("l1", "l4"),
        ("l1", "l5"),
        ("l2", "l5"),
        ("l3", "l5"),
        ("l4", "l8"),
        ("l5", "l8"),
        ("l5", "l9"),
        ("l6", "l9"),
        ("l7", "l10"),
    ]

    for importer, imported in edges:
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES (?, ?, ?, 0)",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def hexagonal_repo_id():
    """ID for hexagonal fixture."""
    return "hexagonal-repo"


@pytest.fixture
def hexagonal_fixture_db(temp_db, hexagonal_repo_id):
    """Canonical hexagonal (ports & adapters) architecture fixture."""
    conn = temp_db.connection()
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (hexagonal_repo_id, "/fixtures/hexagonal", "hexagonal-arch"),
    )

    # Hexagonal: core + 4 adapters
    files = [
        ("h1", "core/domain.py", "python"),
        ("h2", "core/service.py", "python"),
        ("h3", "adapters/web_adapter.py", "python"),
        ("h4", "adapters/db_adapter.py", "python"),
        ("h5", "adapters/cache_adapter.py", "python"),
        ("h6", "adapters/message_adapter.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (file_id, hexagonal_repo_id, rel_path, lang, 100),
        )

    # Hexagonal pattern: adapters depend on core, no cross-adapter deps
    edges = [
        ("h1", "h2"),  # domain ← service
        ("h3", "h1"),  # web → core
        ("h3", "h2"),  # web → service
        ("h4", "h1"),  # db → core
        ("h4", "h2"),  # db → service
        ("h5", "h1"),  # cache → core
        ("h5", "h2"),  # cache → service
        ("h6", "h1"),  # message → core
        ("h6", "h2"),  # message → service
    ]

    for importer, imported in edges:
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES (?, ?, ?, 0)",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def mvc_repo_id():
    """ID for MVC fixture."""
    return "mvc-repo"


@pytest.fixture
def mvc_fixture_db(temp_db, mvc_repo_id):
    """Canonical MVC architecture fixture."""
    conn = temp_db.connection()
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (mvc_repo_id, "/fixtures/mvc", "mvc-arch"),
    )

    # MVC: Model ← Controller ← View (3-tier)
    files = [
        ("m1", "models/user.py", "python"),
        ("m2", "models/order.py", "python"),
        ("m3", "models/product.py", "python"),
        ("m4", "controllers/user_ctrl.py", "python"),
        ("m5", "controllers/order_ctrl.py", "python"),
        ("m6", "views/user_view.py", "python"),
        ("m7", "views/order_view.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (file_id, mvc_repo_id, rel_path, lang, 100),
        )

    # MVC edges: view → controller → model
    edges = [
        ("m6", "m4"),  # user_view → user_ctrl
        ("m7", "m5"),  # order_view → order_ctrl
        ("m4", "m1"),  # user_ctrl → user model
        ("m4", "m3"),  # user_ctrl → product model
        ("m5", "m2"),  # order_ctrl → order model
        ("m5", "m3"),  # order_ctrl → product model
    ]

    for importer, imported in edges:
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES (?, ?, ?, 0)",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def microservices_repo_id():
    """ID for microservices fixture."""
    return "microservices-repo"


@pytest.fixture
def microservices_fixture_db(temp_db, microservices_repo_id):
    """Canonical microservices architecture fixture."""
    conn = temp_db.connection()
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (microservices_repo_id, "/fixtures/microservices", "microservices-arch"),
    )

    # Microservices: 4 independent services with minimal coupling
    files = [
        ("ms1", "auth_service/auth.py", "python"),
        ("ms2", "auth_service/models.py", "python"),
        ("ms3", "payment_service/payment.py", "python"),
        ("ms4", "payment_service/gateway.py", "python"),
        ("ms5", "user_service/user.py", "python"),
        ("ms6", "user_service/profile.py", "python"),
        ("ms7", "notification_service/notif.py", "python"),
        ("ms8", "notification_service/sender.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (file_id, microservices_repo_id, rel_path, lang, 100),
        )

    # Microservices: intra-service dependencies, minimal inter-service
    edges = [
        # Auth service (internal)
        ("ms1", "ms2"),  # auth → models
        # Payment service (internal)
        ("ms3", "ms4"),  # payment → gateway
        # User service (internal)
        ("ms5", "ms6"),  # user → profile
        # Notification service (internal)
        ("ms7", "ms8"),  # notif → sender
        # Only 1 inter-service dependency
        ("ms3", "ms1"),  # payment → auth (minimal coupling)
    ]

    for importer, imported in edges:
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES (?, ?, ?, 0)",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def flat_repo_id():
    """ID for flat fixture."""
    return "flat-repo"


@pytest.fixture
def flat_fixture_db(temp_db, flat_repo_id):
    """Canonical flat/monolithic architecture fixture."""
    conn = temp_db.connection()
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (flat_repo_id, "/fixtures/flat", "flat-arch"),
    )

    # Flat: everything imports everything (no structure)
    files = [
        ("f1", "main.py", "python"),
        ("f2", "auth.py", "python"),
        ("f3", "users.py", "python"),
        ("f4", "orders.py", "python"),
        ("f5", "payments.py", "python"),
        ("f6", "utils.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (file_id, flat_repo_id, rel_path, lang, 100),
        )

    # Flat: dense connectivity (each file imports many others)
    edges = [
        ("f1", "f2"),
        ("f1", "f3"),
        ("f1", "f4"),
        ("f1", "f5"),
        ("f2", "f3"),
        ("f2", "f4"),
        ("f2", "f6"),
        ("f3", "f4"),
        ("f3", "f5"),
        ("f3", "f6"),
        ("f4", "f5"),
        ("f4", "f6"),
        ("f5", "f6"),
    ]

    for importer, imported in edges:
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES (?, ?, ?, 0)",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()
    return temp_db


@pytest.fixture
def ambiguous_repo_id():
    """ID for ambiguous fixture."""
    return "ambiguous-repo"


@pytest.fixture
def ambiguous_fixture_db(temp_db, ambiguous_repo_id):
    """Ambiguous architecture (layered vs MVC)."""
    conn = temp_db.connection()
    conn.execute(
        "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
        (ambiguous_repo_id, "/fixtures/ambiguous", "ambiguous-arch"),
    )

    # Ambiguous: could be layered OR MVC
    files = [
        ("a1", "views/view1.py", "python"),
        ("a2", "views/view2.py", "python"),
        ("a3", "controllers/ctrl1.py", "python"),
        ("a4", "controllers/ctrl2.py", "python"),
        ("a5", "models/model1.py", "python"),
        ("a6", "models/model2.py", "python"),
    ]

    for file_id, rel_path, lang in files:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (file_id, ambiguous_repo_id, rel_path, lang, 100),
        )

    # Ambiguous edges: could be interpreted as layers OR MVC
    edges = [
        ("a1", "a3"),
        ("a1", "a5"),
        ("a2", "a4"),
        ("a2", "a5"),
        ("a3", "a5"),
        ("a4", "a6"),
    ]

    for importer, imported in edges:
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES (?, ?, ?, 0)",
            (importer, imported, "module"),
        )

    conn.commit()
    conn.close()
    return temp_db
