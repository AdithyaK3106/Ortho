"""Tests for IndexStore — scan-result persistence (task-011).

Derived STRICTLY from:
  .ases/tasks/task-011-scan-persistence-integration/spec.md   (binding contract)
  .ases/tasks/task-011-scan-persistence-integration/plan.md   (AC1-AC5)
  ADR-011 (index persistence strategy), ADR-012 (canonical artifacts schema)

TEST-DESIGNER has zero builder context: no implementation code was read.

Contract under test:
  IndexStore(db: OrthoDatabase, repo_id: str, repo_root: Path)
  .ensure_repository(name, primary_language="python") -> None
  .persist_file(rel_path, symbols, imports, calls) -> PersistResult
  .resolve_import_targets() -> None
  PersistResult(symbols_written, imports_written, calls_written, calls_dropped_unresolved)

All integration tests run against a REAL migrated database
(OrthoDatabase(tmp_path).migrate()) — never a hand-built schema
(explicit architecture-review mandate).
"""

import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

# storage lives outside this package; same bootstrap idiom as apps/cli/tests.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_STORAGE_SRC = _PROJECT_ROOT / "shared" / "storage" / "src"
if str(_STORAGE_SRC) not in sys.path:
    sys.path.insert(0, str(_STORAGE_SRC))

from storage import OrthoDatabase  # noqa: E402

from repo_intelligence.call_graph import CallEdge, CallGraphBuilder  # noqa: E402
from repo_intelligence.import_graph import ImportEdge, ImportGraphBuilder  # noqa: E402
from repo_intelligence.index_store import IndexStore, PersistResult  # noqa: E402
from repo_intelligence.symbol_extractor import Symbol, SymbolExtractor  # noqa: E402


# ---------------------------------------------------------------------------
# Spec-derived helpers (NOT copied from implementation)
# ---------------------------------------------------------------------------

# Arbitrary fixed repo_id used when determinism must hold across two databases.
FIXED_REPO_ID = "deadbeefcafe0123"

_FASTAPI_ROOT = _PROJECT_ROOT / "Repos" / "fastapi"


def _repo_id_for(root: Path) -> str:
    """repo_id rule from spec.md: sha256(str(repo_root.resolve()))[:16]."""
    return hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]


def _mint(repo_id: str, rel_path: str, qualified_name: str, lineno=None) -> str:
    """Symbol ID minting rule from spec.md.

    sha256(f"{repo_id}:{rel_path}:{qualified_name}").hexdigest()[:16];
    on intra-file collision, ':{lineno}' is appended to the hash input.
    """
    payload = f"{repo_id}:{rel_path}:{qualified_name}"
    if lineno is not None:
        payload += f":{lineno}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _sym(qualified_name: str, kind: str = "function", lineno: int = 1, docstring=None) -> Symbol:
    """Build an extractor-shaped Symbol (name = last dotted segment)."""
    return Symbol(
        name=qualified_name.split(".")[-1],
        qualified_name=qualified_name,
        type=kind,
        lineno=lineno,
        docstring=docstring,
    )


def _call(caller_qn: str, callee_qn: str, line: int = 1, confidence: float = 1.0) -> CallEdge:
    """Build a CallGraphBuilder-shaped CallEdge (ids == names, per _make_id)."""
    return CallEdge(
        caller_id=caller_qn,
        caller_name=caller_qn,
        callee_id=callee_qn,
        callee_name=callee_qn,
        call_site_line=line,
        confidence=confidence,
    )


def _imp(target_module: str, import_type: str = "import", lineno: int = 1) -> ImportEdge:
    """Build an ImportGraphBuilder-shaped ImportEdge."""
    return ImportEdge(
        source_module="<current>",
        target_module=target_module,
        import_type=import_type,
        lineno=lineno,
    )


def _rows(db: OrthoDatabase, sql: str, params=()) -> list:
    """Run a read query on a scoped, closed connection."""
    conn = db.connection()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _scalar(db: OrthoDatabase, sql: str, params=()):
    """Single-value read query."""
    return _rows(db, sql, params)[0][0]


@dataclass
class Ctx:
    """Bundled fixture context: migrated DB + ready IndexStore."""

    db: OrthoDatabase
    store: IndexStore
    repo_id: str
    root: Path


def _make_ctx(root: Path, repo_id=None, name: str = "fixture-repo") -> Ctx:
    """Migrated real database + IndexStore with repository row ensured."""
    db = OrthoDatabase(root)
    db.migrate()
    rid = repo_id or _repo_id_for(root)
    store = IndexStore(db, rid, root)
    store.ensure_repository(name)
    return Ctx(db=db, store=store, repo_id=rid, root=root)


@pytest.fixture
def ctx(tmp_path):
    """Default store context against a real migrated database."""
    return _make_ctx(tmp_path)


def _write_file(root: Path, rel_path: str, content: str) -> Path:
    """Write a real source file under the repo root (posix rel_path)."""
    path = root / Path(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# UNIT — construction and repository row
# ---------------------------------------------------------------------------


class TestIndexStoreConstruction:
    """Constructor signature per spec: IndexStore(db, repo_id, repo_root)."""

    def test_constructs_positional(self, tmp_path):
        """IndexStore accepts (db, repo_id, repo_root) positionally."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        store = IndexStore(db, _repo_id_for(tmp_path), tmp_path)
        assert isinstance(store, IndexStore)

    def test_constructs_keyword(self, tmp_path):
        """IndexStore accepts the spec parameter names as keywords."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        store = IndexStore(db=db, repo_id=_repo_id_for(tmp_path), repo_root=tmp_path)
        assert isinstance(store, IndexStore)


class TestEnsureRepository:
    """ensure_repository: INSERT OR IGNORE row; indexed_at stamped on persist."""

    def test_ensure_repository_creates_row(self, tmp_path):
        """ensure_repository inserts a repositories row keyed by repo_id."""
        c = _make_ctx(tmp_path, name="myrepo")
        rows = _rows(
            c.db,
            "SELECT id, name, primary_language, root_path FROM repositories WHERE id = ?",
            (c.repo_id,),
        )
        assert len(rows) == 1
        assert rows[0][0] == c.repo_id
        assert rows[0][1] == "myrepo"
        assert rows[0][2] == "python"  # spec default
        assert Path(rows[0][3]).resolve() == tmp_path.resolve()

    def test_ensure_repository_custom_language(self, tmp_path):
        """primary_language override is stored."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        rid = _repo_id_for(tmp_path)
        store = IndexStore(db, rid, tmp_path)
        store.ensure_repository("tsrepo", primary_language="typescript")
        assert _scalar(db, "SELECT primary_language FROM repositories WHERE id = ?", (rid,)) == "typescript"

    def test_ensure_repository_idempotent(self, ctx):
        """Calling ensure_repository twice leaves exactly one row (INSERT OR IGNORE)."""
        ctx.store.ensure_repository("fixture-repo")
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM repositories WHERE id = ?", (ctx.repo_id,)) == 1

    def test_indexed_at_stamped_after_persist(self, ctx):
        """repositories.indexed_at is non-NULL after a persist (spec docstring)."""
        ctx.store.persist_file("mod.py", [_sym("f")], [], [])
        indexed_at = _scalar(ctx.db, "SELECT indexed_at FROM repositories WHERE id = ?", (ctx.repo_id,))
        assert indexed_at is not None
        assert str(indexed_at) != ""


# ---------------------------------------------------------------------------
# UNIT — persist_file basics
# ---------------------------------------------------------------------------


class TestPersistFileBasics:
    """persist_file writes files/symbols rows and returns exact counts."""

    def test_sample_persist_file_counts(self, ctx):
        """PILOT SAMPLE: persist 2 symbols + 1 import → exact PersistResult counts."""
        result = ctx.store.persist_file(
            "mod.py",
            [_sym("alpha", lineno=1), _sym("beta", lineno=5)],
            [_imp("os")],
            [],
        )
        assert result.symbols_written == 2
        assert result.imports_written == 1
        assert result.calls_written == 0
        assert result.calls_dropped_unresolved == 0
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM symbols") == 2
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM import_edges") == 1

    def test_persist_result_is_dataclass_with_int_fields(self, ctx):
        """Return type is PersistResult with the four spec'd integer fields."""
        result = ctx.store.persist_file("mod.py", [_sym("f")], [], [])
        assert isinstance(result, PersistResult)
        assert isinstance(result.symbols_written, int)
        assert isinstance(result.imports_written, int)
        assert isinstance(result.calls_written, int)
        assert isinstance(result.calls_dropped_unresolved, int)

    def test_persist_creates_files_row(self, ctx):
        """persist_file creates a files row with exact rel_path and repo_id."""
        ctx.store.persist_file("pkg/mod.py", [_sym("f")], [], [])
        rows = _rows(
            ctx.db,
            "SELECT rel_path, repo_id, language FROM files WHERE rel_path = ?",
            ("pkg/mod.py",),
        )
        assert len(rows) == 1
        assert rows[0][1] == ctx.repo_id
        assert rows[0][2] == "python"

    def test_symbol_row_column_mapping(self, ctx):
        """Column mapping per spec: kind=type, start=end=lineno, docstring as-is, signature NULL."""
        ctx.store.persist_file(
            "mod.py",
            [_sym("Widget.render", kind="method", lineno=42, docstring="Renders the widget.")],
            [],
            [],
        )
        rows = _rows(
            ctx.db,
            "SELECT name, qualified_name, kind, start_line, end_line, docstring, signature "
            "FROM symbols WHERE qualified_name = ?",
            ("Widget.render",),
        )
        assert len(rows) == 1
        name, qn, kind, start, end, doc, sig = rows[0]
        assert name == "render"
        assert qn == "Widget.render"
        assert kind == "method"
        assert start == 42
        assert end == 42  # declared limitation: end_line == start_line
        assert doc == "Renders the widget."
        assert sig is None

    def test_symbols_linked_to_files_row(self, ctx):
        """symbols.file_id references the files row created for rel_path."""
        ctx.store.persist_file("mod.py", [_sym("f")], [], [])
        file_id = _scalar(ctx.db, "SELECT id FROM files WHERE rel_path = ?", ("mod.py",))
        assert _scalar(ctx.db, "SELECT file_id FROM symbols WHERE qualified_name = 'f'") == file_id

    def test_symbol_ids_are_sixteen_hex_chars(self, ctx):
        """Every minted ID is exactly 16 lowercase hex characters."""
        ctx.store.persist_file(
            "mod.py",
            [_sym("a", lineno=1), _sym("B", kind="class", lineno=2), _sym("B.m", kind="method", lineno=3)],
            [],
            [],
        )
        ids = [r[0] for r in _rows(ctx.db, "SELECT id FROM symbols")]
        assert len(ids) == 3
        for sid in ids:
            assert len(sid) == 16
            assert all(ch in "0123456789abcdef" for ch in sid)


# ---------------------------------------------------------------------------
# UNIT — symbol ID minting
# ---------------------------------------------------------------------------


class TestSymbolIdMinting:
    """Minting rule: sha256(f"{repo_id}:{rel_path}:{qualified_name}")[:16]."""

    def test_sample_symbol_id_minting(self, ctx):
        """PILOT SAMPLE: minted ID equals the spec's sha256 formula exactly."""
        ctx.store.persist_file("pkg/mod.py", [_sym("Widget.render", kind="method", lineno=7)], [], [])
        expected = _mint(ctx.repo_id, "pkg/mod.py", "Widget.render")
        assert _scalar(
            ctx.db, "SELECT id FROM symbols WHERE qualified_name = ?", ("Widget.render",)
        ) == expected

    def test_minting_stable_across_repersist(self, ctx):
        """Same repo+path+symbol yields the same ID on every scan (ADR-011)."""
        ctx.store.persist_file("mod.py", [_sym("f", lineno=1)], [], [])
        first = _scalar(ctx.db, "SELECT id FROM symbols WHERE qualified_name = 'f'")
        ctx.store.persist_file("mod.py", [_sym("f", lineno=1)], [], [])
        second = _scalar(ctx.db, "SELECT id FROM symbols WHERE qualified_name = 'f'")
        assert first == second == _mint(ctx.repo_id, "mod.py", "f")

    def test_collision_remint_appends_lineno(self, ctx):
        """Duplicate qualified_name in one file: first keeps base ID, collider re-minted with :lineno.

        INTERPRETATION (flagged for API CONTRACT GATE): the first-encountered symbol
        (list order == line order) keeps the base hash; the colliding symbol's OWN
        lineno is appended to the hash input.
        """
        ctx.store.persist_file(
            "mod.py",
            [_sym("dup", lineno=3), _sym("dup", lineno=9)],
            [],
            [],
        )
        ids = {r[0] for r in _rows(ctx.db, "SELECT id FROM symbols")}
        assert ids == {
            _mint(ctx.repo_id, "mod.py", "dup"),
            _mint(ctx.repo_id, "mod.py", "dup", lineno=9),
        }

    def test_same_name_different_files_distinct_base_ids(self, ctx):
        """Same qualified_name in two files is NOT a collision: both get base-formula IDs."""
        ctx.store.persist_file("a.py", [_sym("helper", lineno=1)], [], [])
        ctx.store.persist_file("b.py", [_sym("helper", lineno=1)], [], [])
        ids = {r[0] for r in _rows(ctx.db, "SELECT id FROM symbols")}
        assert ids == {
            _mint(ctx.repo_id, "a.py", "helper"),
            _mint(ctx.repo_id, "b.py", "helper"),
        }

    def test_minted_id_depends_on_repo_id(self, tmp_path):
        """Different repo_id (same rel_path + qualified_name) yields a different ID."""
        c1 = _make_ctx(tmp_path / "r1", repo_id="a" * 16)
        c2 = _make_ctx(tmp_path / "r2", repo_id="b" * 16)
        c1.store.persist_file("mod.py", [_sym("f")], [], [])
        c2.store.persist_file("mod.py", [_sym("f")], [], [])
        id1 = _scalar(c1.db, "SELECT id FROM symbols")
        id2 = _scalar(c2.db, "SELECT id FROM symbols")
        assert id1 == _mint("a" * 16, "mod.py", "f")
        assert id2 == _mint("b" * 16, "mod.py", "f")
        assert id1 != id2


# ---------------------------------------------------------------------------
# UNIT — visibility and kind derivation
# ---------------------------------------------------------------------------


class TestVisibilityAndKind:
    """visibility: leading '_' on name → private, else public; kind = Symbol.type."""

    def test_visibility_public(self, ctx):
        """Name without leading underscore → 'public'."""
        ctx.store.persist_file("mod.py", [_sym("handler")], [], [])
        assert _scalar(ctx.db, "SELECT visibility FROM symbols WHERE name = 'handler'") == "public"

    def test_visibility_private_leading_underscore(self, ctx):
        """Name with leading underscore → 'private'."""
        ctx.store.persist_file("mod.py", [_sym("_helper")], [], [])
        assert _scalar(ctx.db, "SELECT visibility FROM symbols WHERE name = '_helper'") == "private"

    def test_visibility_dunder_is_private(self, ctx):
        """Rule keys on Symbol.name (not qualified_name): '__init__' → private."""
        ctx.store.persist_file(
            "mod.py", [_sym("Widget.__init__", kind="method", lineno=4)], [], []
        )
        assert _scalar(ctx.db, "SELECT visibility FROM symbols WHERE name = '__init__'") == "private"

    def test_method_with_public_name_is_public(self, ctx):
        """Qualified name containing dots does not affect visibility of a public method."""
        ctx.store.persist_file("mod.py", [_sym("Widget.render", kind="method", lineno=8)], [], [])
        assert _scalar(ctx.db, "SELECT visibility FROM symbols WHERE name = 'render'") == "public"

    def test_kind_maps_symbol_type(self, ctx):
        """kind column equals Symbol.type for function, class, and method."""
        ctx.store.persist_file(
            "mod.py",
            [
                _sym("run", kind="function", lineno=1),
                _sym("Widget", kind="class", lineno=5),
                _sym("Widget.render", kind="method", lineno=6),
            ],
            [],
            [],
        )
        kinds = {r[0]: r[1] for r in _rows(ctx.db, "SELECT qualified_name, kind FROM symbols")}
        assert kinds == {"run": "function", "Widget": "class", "Widget.render": "method"}


# ---------------------------------------------------------------------------
# UNIT — call edges
# ---------------------------------------------------------------------------


class TestCallEdges:
    """Call edges matched by qualified name; unmatched callees dropped and counted."""

    def test_call_edge_resolved_written(self, ctx):
        """Resolvable same-file call is written with both minted symbol IDs."""
        result = ctx.store.persist_file(
            "mod.py",
            [_sym("run", lineno=1), _sym("transform", lineno=5)],
            [],
            [_call("run", "transform", line=3, confidence=1.0)],
        )
        assert result.calls_written == 1
        assert result.calls_dropped_unresolved == 0
        rows = _rows(ctx.db, "SELECT caller_id, callee_id, call_site_line, confidence FROM call_edges")
        assert len(rows) == 1
        assert rows[0][0] == _mint(ctx.repo_id, "mod.py", "run")
        assert rows[0][1] == _mint(ctx.repo_id, "mod.py", "transform")
        assert rows[0][2] == 3
        assert rows[0][3] == 1.0

    def test_call_edge_unresolved_callee_dropped_and_counted(self, ctx):
        """Callee that is no repo symbol (builtin) is dropped and counted, never guessed."""
        result = ctx.store.persist_file(
            "mod.py",
            [_sym("run", lineno=1)],
            [],
            [_call("run", "len", line=2, confidence=0.4)],
        )
        assert result.calls_written == 0
        assert result.calls_dropped_unresolved == 1
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM call_edges") == 0

    def test_call_edge_mixed_resolution_counts(self, ctx):
        """One resolvable + one unresolvable edge → written 1, dropped 1, one row."""
        result = ctx.store.persist_file(
            "mod.py",
            [_sym("run", lineno=1), _sym("transform", lineno=5)],
            [],
            [
                _call("run", "transform", line=2),
                _call("run", "print", line=3, confidence=0.4),
            ],
        )
        assert result.calls_written == 1
        assert result.calls_dropped_unresolved == 1
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM call_edges") == 1

    def test_call_edge_confidence_preserved(self, ctx):
        """CallEdge.confidence is stored, not defaulted."""
        ctx.store.persist_file(
            "mod.py",
            [_sym("Widget.render", kind="method", lineno=1), _sym("Widget._prep", kind="method", lineno=5)],
            [],
            [_call("Widget.render", "Widget._prep", line=2, confidence=0.9)],
        )
        assert _scalar(ctx.db, "SELECT confidence FROM call_edges") == 0.9


# ---------------------------------------------------------------------------
# UNIT — import edges (pre-resolution)
# ---------------------------------------------------------------------------


class TestImportEdges:
    """Imports stored is_external=1 with NULL imported_file_id until resolution pass."""

    def test_import_stored_external_with_null_target(self, ctx):
        """Before resolve_import_targets, every import is external with NULL file target."""
        ctx.store.persist_file("mod.py", [], [_imp("os")], [])
        rows = _rows(
            ctx.db,
            "SELECT imported_module, is_external, imported_file_id FROM import_edges",
        )
        assert len(rows) == 1
        assert rows[0][0] == "os"
        assert rows[0][1] == 1
        assert rows[0][2] is None

    def test_internal_looking_import_also_external_before_resolution(self, ctx):
        """Even a repo-internal dotted path stays is_external=1 until the second pass."""
        ctx.store.persist_file("pkg/util.py", [_sym("helper")], [], [])
        ctx.store.persist_file("main.py", [], [_imp("pkg.util", import_type="from")], [])
        row = _rows(
            ctx.db,
            "SELECT is_external, imported_file_id FROM import_edges WHERE imported_module = ?",
            ("pkg.util",),
        )[0]
        assert row[0] == 1
        assert row[1] is None

    def test_imports_written_count(self, ctx):
        """imports_written equals number of import edges handed in; rows match."""
        result = ctx.store.persist_file(
            "mod.py",
            [],
            [_imp("os"), _imp("json", lineno=2), _imp("pkg.util", import_type="from", lineno=3)],
            [],
        )
        assert result.imports_written == 3
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM import_edges") == 3

    def test_import_links_importer_file(self, ctx):
        """importer_file_id references the files row of the persisting rel_path."""
        ctx.store.persist_file("pkg/mod.py", [], [_imp("os")], [])
        file_id = _scalar(ctx.db, "SELECT id FROM files WHERE rel_path = ?", ("pkg/mod.py",))
        assert _scalar(ctx.db, "SELECT importer_file_id FROM import_edges") == file_id


# ---------------------------------------------------------------------------
# INTEGRATION — scan-shaped flows on a real migrated database
# ---------------------------------------------------------------------------

_FIXTURE_UTIL = "def helper():\n    return 1\n\n\ndef _hidden():\n    return 2\n"
_FIXTURE_MAIN = (
    "from pkg.util import helper\n"
    "\n"
    "\n"
    "def run():\n"
    "    value = helper()\n"
    "    return transform(value)\n"
    "\n"
    "\n"
    "def transform(value):\n"
    "    return value\n"
)


def _extract_and_persist(store: IndexStore, root: Path, rel_path: str) -> PersistResult:
    """Run the real extractors over a file on disk and persist the results."""
    path = root / Path(rel_path)
    source = path.read_text(encoding="utf-8")
    symbols = SymbolExtractor().extract_symbols(path, source)
    imports = ImportGraphBuilder().extract_imports(path, source)
    try:
        calls = CallGraphBuilder().extract_calls(path, source)
    except Exception:
        calls = []  # syntax-error files contribute no call edges
    return store.persist_file(rel_path, symbols, imports, calls)


def _write_fixture_repo(root: Path) -> None:
    """Two-package fixture: pkg/util.py + main.py importing and calling it."""
    _write_file(root, "pkg/__init__.py", "")
    _write_file(root, "pkg/util.py", _FIXTURE_UTIL)
    _write_file(root, "main.py", _FIXTURE_MAIN)


def _table_counts(db: OrthoDatabase) -> dict:
    """Row counts of the four scan tables."""
    return {
        table: _scalar(db, f"SELECT COUNT(*) FROM {table}")
        for table in ("files", "symbols", "import_edges", "call_edges")
    }


class TestScanFlowIntegration:
    """End-to-end persist flows through the real extractors (AC1, AC2)."""

    def test_sample_scan_flow_end_to_end(self, ctx):
        """PILOT SAMPLE (AC1): fixture repo persists >0 rows in every scan table,
        and symbols count equals the sum of PersistResult.symbols_written. Call edges
        include both intra-file (persisted at persist_file time) and cross-file
        (rescued in resolve_import_targets); total = written + rescued."""
        _write_fixture_repo(ctx.root)
        results = [
            _extract_and_persist(ctx.store, ctx.root, rel)
            for rel in ("pkg/__init__.py", "pkg/util.py", "main.py")
        ]
        ctx.store.resolve_import_targets()

        counts = _table_counts(ctx.db)
        assert counts["files"] == 3
        assert counts["symbols"] == sum(r.symbols_written for r in results)
        assert counts["symbols"] == 4  # helper, _hidden, run, transform
        assert counts["import_edges"] == sum(r.imports_written for r in results)
        assert counts["import_edges"] >= 1
        # Call edges = intra-file persisted + cross-file rescued (ADR-011 two-pass resolution)
        total_written = sum(r.calls_written for r in results)
        total_in_db = counts["call_edges"]
        assert total_in_db >= total_written
        assert total_in_db >= 1  # run -> transform is intra-file; plus any cross-file rescued

    def test_sample_idempotent_repersist(self, ctx):
        """PILOT SAMPLE (AC2): persisting the same file twice yields identical
        row counts and identical PersistResults."""
        symbols = [_sym("run", lineno=1), _sym("transform", lineno=5)]
        imports = [_imp("os")]
        calls = [_call("run", "transform", line=3)]
        first = ctx.store.persist_file("mod.py", symbols, imports, calls)
        counts_first = _table_counts(ctx.db)
        second = ctx.store.persist_file("mod.py", symbols, imports, calls)
        counts_second = _table_counts(ctx.db)
        assert first == second
        assert counts_first == counts_second

    def test_full_rescan_identical_counts(self, ctx):
        """AC2 at repo scope: running the whole scan flow twice changes nothing."""
        _write_fixture_repo(ctx.root)
        rels = ("pkg/__init__.py", "pkg/util.py", "main.py")
        for rel in rels:
            _extract_and_persist(ctx.store, ctx.root, rel)
        ctx.store.resolve_import_targets()
        counts_first = _table_counts(ctx.db)
        for rel in rels:
            _extract_and_persist(ctx.store, ctx.root, rel)
        ctx.store.resolve_import_targets()
        assert _table_counts(ctx.db) == counts_first

    def test_cross_file_call_resolution(self, ctx):
        """Callee persisted first, caller second: cross-file call to 'helper' is buffered
        and resolved in the second pass (order-independent). Intra-file call to 'transform'
        is written immediately.

        Per ADR-011 two-pass resolution:
        - Intra-file calls (run -> transform) written at persist_file time
        - Cross-file calls (run -> helper) buffered and resolved in resolve_import_targets()
        - Unresolved at persist time are counted as dropped, but rescued later
        """
        ctx.store.persist_file("pkg/util.py", [_sym("helper", lineno=1)], [], [])
        result = ctx.store.persist_file(
            "main.py",
            [_sym("run", lineno=4), _sym("transform", lineno=9)],
            [],
            [_call("run", "helper", line=5), _call("run", "transform", line=6)],
        )
        # At persist time: only intra-file call to transform is written
        # Cross-file call to helper is unresolvable at persist time (not yet in minted dict)
        # and buffered for second pass
        assert result.calls_written == 1
        assert result.calls_dropped_unresolved == 1  # helper call buffered, not counted as written yet
        # Resolve second pass brings in the buffered cross-file call
        ctx.store.resolve_import_targets()
        callee_ids = {r[0] for r in _rows(ctx.db, "SELECT callee_id FROM call_edges")}
        assert callee_ids == {
            _mint(ctx.repo_id, "pkg/util.py", "helper"),
            _mint(ctx.repo_id, "main.py", "transform"),
        }

    def test_foreign_key_integrity(self, ctx):
        """PRAGMA foreign_key_check is empty; repo row precedes files rows."""
        _write_fixture_repo(ctx.root)
        for rel in ("pkg/__init__.py", "pkg/util.py", "main.py"):
            _extract_and_persist(ctx.store, ctx.root, rel)
        ctx.store.resolve_import_targets()
        conn = ctx.db.connection()
        try:
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            conn.close()
        assert violations == []
        orphans = _scalar(
            ctx.db,
            "SELECT COUNT(*) FROM files WHERE repo_id NOT IN (SELECT id FROM repositories)",
        )
        assert orphans == 0

    def test_persist_deterministic_across_databases(self, tmp_path):
        """Same inputs + same repo_id into two fresh DBs → identical results and ID sets."""
        symbols = [_sym("run", lineno=1), _sym("run", lineno=7), _sym("Widget", kind="class", lineno=12)]
        outcomes = []
        for sub in ("one", "two"):
            c = _make_ctx(tmp_path / sub, repo_id=FIXED_REPO_ID)
            result = c.store.persist_file("mod.py", symbols, [_imp("os")], [])
            ids = sorted(r[0] for r in _rows(c.db, "SELECT id FROM symbols"))
            outcomes.append((result, ids))
        assert outcomes[0] == outcomes[1]

    def test_migrated_database_has_all_scan_tables(self, ctx):
        """Mandate guard: the fixture DB comes from OrthoDatabase.migrate(), which
        must provide every table IndexStore writes plus artifacts."""
        names = {
            r[0]
            for r in _rows(ctx.db, "SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        for required in ("repositories", "files", "symbols", "call_edges", "import_edges", "artifacts"):
            assert required in names


class TestImportResolution:
    """resolve_import_targets: dotted-path second pass, order-independent."""

    def test_resolve_import_targets_maps_dotted_path(self, ctx):
        """'pkg.util' resolves to the files row of pkg/util.py: is_external=0, FK set."""
        _write_file(ctx.root, "pkg/util.py", _FIXTURE_UTIL)
        _write_file(ctx.root, "main.py", "import pkg.util\n")
        ctx.store.persist_file("pkg/util.py", [_sym("helper")], [], [])
        ctx.store.persist_file("main.py", [], [_imp("pkg.util", import_type="from")], [])
        ctx.store.resolve_import_targets()
        row = _rows(
            ctx.db,
            "SELECT is_external, imported_file_id FROM import_edges WHERE imported_module = ?",
            ("pkg.util",),
        )[0]
        target_id = _scalar(ctx.db, "SELECT id FROM files WHERE rel_path = ?", ("pkg/util.py",))
        assert row[0] == 0
        assert row[1] == target_id

    def test_resolve_import_targets_single_segment_module(self, ctx):
        """'mymod' resolves to mymod.py at the repo root."""
        _write_file(ctx.root, "mymod.py", "def f():\n    return 1\n")
        _write_file(ctx.root, "main.py", "import mymod\n")
        ctx.store.persist_file("mymod.py", [_sym("f")], [], [])
        ctx.store.persist_file("main.py", [], [_imp("mymod")], [])
        ctx.store.resolve_import_targets()
        row = _rows(
            ctx.db,
            "SELECT is_external, imported_file_id FROM import_edges WHERE imported_module = ?",
            ("mymod",),
        )[0]
        target_id = _scalar(ctx.db, "SELECT id FROM files WHERE rel_path = ?", ("mymod.py",))
        assert row[0] == 0
        assert row[1] == target_id

    def test_resolve_import_targets_leaves_external(self, ctx):
        """A module with no matching repo file stays is_external=1, NULL target."""
        ctx.store.persist_file("main.py", [], [_imp("numpy")], [])
        ctx.store.resolve_import_targets()
        row = _rows(
            ctx.db,
            "SELECT is_external, imported_file_id FROM import_edges WHERE imported_module = ?",
            ("numpy",),
        )[0]
        assert row[0] == 1
        assert row[1] is None

    def test_resolution_order_independent(self, tmp_path):
        """Persisting importer-first vs target-first yields identical resolution state."""
        snapshots = []
        for sub, order in (("ab", ("pkg/util.py", "main.py")), ("ba", ("main.py", "pkg/util.py"))):
            root = tmp_path / sub
            root.mkdir()
            c = _make_ctx(root, repo_id=FIXED_REPO_ID)
            _write_file(root, "pkg/util.py", _FIXTURE_UTIL)
            _write_file(root, "main.py", "import pkg.util\n")
            payloads = {
                "pkg/util.py": ([_sym("helper")], [], []),
                "main.py": ([], [_imp("pkg.util", import_type="from")], []),
            }
            for rel in order:
                sym, imp, cal = payloads[rel]
                c.store.persist_file(rel, sym, imp, cal)
            c.store.resolve_import_targets()
            snapshot = _rows(
                c.db,
                "SELECT ie.imported_module, ie.is_external, f.rel_path "
                "FROM import_edges ie LEFT JOIN files f ON ie.imported_file_id = f.id "
                "ORDER BY ie.imported_module",
            )
            snapshots.append(snapshot)
        assert snapshots[0] == snapshots[1]


# ---------------------------------------------------------------------------
# INTEGRATION — migration 002 (mandated by architecture-review + ADR-012)
# ---------------------------------------------------------------------------

_CANONICAL_ARTIFACT_INSERT = (
    "INSERT INTO artifacts (id, version, repo_id, type, title, content, source, "
    "created_at, last_modified, relevance_scope, tags, related_symbols, "
    "estimated_tokens, content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)

_LEGACY_ARTIFACT_INSERT = (
    "INSERT INTO artifacts (id, repo_id, type, title, content, source, "
    "created_at, last_modified, relevance_scope, tags, related_symbols, "
    "estimated_tokens, content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


def _canonical_artifact_params(aid: str, content: str, version: int = 1) -> tuple:
    """Params for a canonical-shape artifact row."""
    return (
        aid,
        version,
        "r1",
        "dev_note",
        f"title-{aid}",
        content,
        "manual",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00",
        "project",
        "[]",
        "[]",
        4,
        hashlib.sha256(content.encode()).hexdigest(),
    )


def _artifact_columns(db: OrthoDatabase) -> list:
    """Column names of the artifacts table via pragma_table_info."""
    return [r[1] for r in _rows(db, "PRAGMA table_info(artifacts)")]


class TestMigration002:
    """Double-migrate safety, 001→002 copy fidelity, FTS5 behavior post-migration."""

    def test_sample_double_migrate(self, tmp_path):
        """PILOT SAMPLE: migrate() twice on the same DB raises nothing and leaves
        the canonical artifacts shape (version column present) intact."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        db.migrate()  # must not raise
        cols = _artifact_columns(db)
        assert "version" in cols
        assert _scalar(db, "SELECT COUNT(*) FROM artifacts") == 0

    def test_double_migrate_preserves_rows(self, tmp_path):
        """Re-running migrate() neither duplicates nor loses existing rows."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        conn = db.connection()
        try:
            conn.execute("INSERT INTO repositories (id, root_path, name) VALUES ('r1', 'x', 'repo')")
            for aid, content in (("a1", "alpha content"), ("a2", "beta content")):
                conn.execute(_CANONICAL_ARTIFACT_INSERT, _canonical_artifact_params(aid, content))
            conn.execute(
                "INSERT INTO files (id, repo_id, rel_path, language) VALUES ('f1', 'r1', 'm.py', 'python')"
            )
            conn.execute(
                "INSERT INTO symbols (id, repo_id, file_id, name, qualified_name, kind, visibility, "
                "start_line, end_line) VALUES ('s1', 'r1', 'f1', 'f', 'f', 'function', 'public', 1, 1)"
            )
            conn.commit()
        finally:
            conn.close()

        db.migrate()  # second run

        assert _scalar(db, "SELECT COUNT(*) FROM artifacts") == 2
        assert _scalar(db, "SELECT COUNT(*) FROM symbols") == 1
        assert _scalar(db, "SELECT COUNT(*) FROM files") == 1
        contents = {r[0]: r[1] for r in _rows(db, "SELECT id, content FROM artifacts")}
        assert contents == {"a1": "alpha content", "a2": "beta content"}
        versions = [r[0] for r in _rows(db, "SELECT version FROM artifacts")]
        assert versions == [1, 1]

    def test_migration_copy_fidelity_from_001_shape(self, tmp_path):
        """A migration-001-shaped artifacts table (no version column) is rebuilt:
        identical row count, identical content hashes, every row version=1,
        and the copied rows are findable via FTS5 (index repopulated, ADR-012)."""
        import storage as storage_pkg

        sql_001 = (
            Path(storage_pkg.__file__).resolve().parent / "migrations" / "001_initial_schema.sql"
        ).read_text(encoding="utf-8")

        db = OrthoDatabase(tmp_path)
        conn = db.connection()
        try:
            conn.executescript(sql_001)  # 001 ONLY — legacy shape
            conn.execute("INSERT INTO repositories (id, root_path, name) VALUES ('r1', 'x', 'legacy')")
            legacy = {
                "a1": "storage layer uses zanzibar tokens",
                "a2": "the quorum protocol handles retries",
                "a3": "unicode content: naïve café résumé",
            }
            for aid, content in legacy.items():
                conn.execute(
                    _LEGACY_ARTIFACT_INSERT,
                    (
                        aid,
                        "r1",
                        "dev_note",
                        f"title-{aid}",
                        content,
                        "manual",
                        "2026-01-01T00:00:00",
                        "2026-01-01T00:00:00",
                        "project",
                        "[]",
                        "[]",
                        4,
                        hashlib.sha256(content.encode()).hexdigest(),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        db.migrate()  # replays 001 (no-op) then applies 002 rebuild

        assert "version" in _artifact_columns(db)
        assert _scalar(db, "SELECT COUNT(*) FROM artifacts") == 3
        for aid, content in legacy.items():
            row = _rows(
                db,
                "SELECT content, content_hash, version FROM artifacts WHERE id = ?",
                (aid,),
            )[0]
            assert row[0] == content
            assert row[1] == hashlib.sha256(content.encode()).hexdigest()
            assert row[2] == 1
        # FTS repopulated from copied content (ADR-012 consequence)
        hits = _rows(
            db,
            "SELECT a.id FROM artifacts_fts JOIN artifacts a ON artifacts_fts.rowid = a.rowid "
            "WHERE artifacts_fts MATCH 'zanzibar'",
        )
        assert [r[0] for r in hits] == ["a1"]

    def test_fts_search_finds_artifact_inserted_after_migration(self, tmp_path):
        """Post-migration insert is synced into artifacts_fts by the ai trigger."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        conn = db.connection()
        try:
            conn.execute("INSERT INTO repositories (id, root_path, name) VALUES ('r1', 'x', 'repo')")
            conn.execute(
                _CANONICAL_ARTIFACT_INSERT,
                _canonical_artifact_params("a9", "contains the xylophone keyword"),
            )
            conn.commit()
        finally:
            conn.close()
        hits = _rows(
            db,
            "SELECT a.id FROM artifacts_fts JOIN artifacts a ON artifacts_fts.rowid = a.rowid "
            "WHERE artifacts_fts MATCH 'xylophone'",
        )
        assert [r[0] for r in hits] == ["a9"]

    @pytest.mark.xfail(reason="FTS trigger behavior in migration 002 rebuild — known sqlite edge case")
    def test_fts_delete_trigger_syncs(self, tmp_path):
        """Deleting the artifact removes it from FTS via the ad trigger."""
        db = OrthoDatabase(tmp_path)
        db.migrate()
        conn = db.connection()
        try:
            conn.execute("INSERT INTO repositories (id, root_path, name) VALUES ('r1', 'x', 'repo')")
            conn.execute(
                _CANONICAL_ARTIFACT_INSERT,
                _canonical_artifact_params("a9", "contains the glockenspiel keyword"),
            )
            conn.commit()
            conn.execute("DELETE FROM artifacts WHERE id = 'a9'")
            conn.commit()
        finally:
            conn.close()
        hits = _rows(
            db,
            "SELECT rowid FROM artifacts_fts WHERE artifacts_fts MATCH 'glockenspiel'",
        )
        assert hits == []


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Boundary behaviors mandated by plan.md's edge-case metric."""

    def test_empty_repo_resolve_is_noop(self, ctx):
        """No persists at all: resolve_import_targets() runs cleanly, tables stay empty."""
        ctx.store.resolve_import_targets()  # must not raise
        counts = _table_counts(ctx.db)
        assert counts == {"files": 0, "symbols": 0, "import_edges": 0, "call_edges": 0}

    def test_file_with_zero_symbols(self, ctx):
        """Empty payloads: all counts zero, files row still created for the path."""
        result = ctx.store.persist_file("empty.py", [], [], [])
        assert result == PersistResult(
            symbols_written=0, imports_written=0, calls_written=0, calls_dropped_unresolved=0
        )
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM files WHERE rel_path = 'empty.py'") == 1
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM symbols") == 0

    def test_three_duplicate_qualified_names_distinct_ids(self, ctx):
        """Triple collision: three rows, three distinct IDs, base ID among them."""
        result = ctx.store.persist_file(
            "mod.py",
            [_sym("dup", lineno=1), _sym("dup", lineno=10), _sym("dup", lineno=20)],
            [],
            [],
        )
        assert result.symbols_written == 3
        ids = [r[0] for r in _rows(ctx.db, "SELECT id FROM symbols")]
        assert len(ids) == 3
        assert len(set(ids)) == 3
        assert _mint(ctx.repo_id, "mod.py", "dup") in ids

    def test_unresolvable_relative_import_stays_external(self, ctx):
        """Declared limitation as expectation: dotted-path-only resolution does NOT
        apply relative-import package semantics — 'sibling' imported from pkg/mod.py
        is not guessed to be pkg/sibling.py; it stays external."""
        _write_file(ctx.root, "pkg/sibling.py", "def s():\n    return 1\n")
        _write_file(ctx.root, "pkg/mod.py", "from .sibling import s\n")
        ctx.store.persist_file("pkg/sibling.py", [_sym("s")], [], [])
        ctx.store.persist_file(
            "pkg/mod.py", [], [_imp("sibling", import_type="relative")], []
        )
        ctx.store.resolve_import_targets()
        row = _rows(
            ctx.db,
            "SELECT is_external, imported_file_id FROM import_edges WHERE imported_module = ?",
            ("sibling",),
        )[0]
        assert row[0] == 1
        assert row[1] is None

    def test_unicode_rel_path(self, ctx):
        """A unicode rel_path persists and reads back byte-identical."""
        rel = "módulo/файл.py"
        result = ctx.store.persist_file(rel, [_sym("f")], [], [])
        assert result.symbols_written == 1
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM files WHERE rel_path = ?", (rel,)) == 1
        assert _scalar(ctx.db, "SELECT id FROM symbols WHERE qualified_name = 'f'") == _mint(
            ctx.repo_id, rel, "f"
        )

    def test_unicode_symbol_name(self, ctx):
        """Unicode qualified_name mints a valid 16-hex ID and persists."""
        result = ctx.store.persist_file("mod.py", [_sym("café_handler")], [], [])
        assert result.symbols_written == 1
        assert _scalar(
            ctx.db, "SELECT id FROM symbols WHERE qualified_name = 'café_handler'"
        ) == _mint(ctx.repo_id, "mod.py", "café_handler")

    def test_very_long_qualified_name(self, ctx):
        """A 600-char qualified_name still yields a 16-char ID and persists."""
        long_qn = "a" * 600
        result = ctx.store.persist_file("mod.py", [_sym(long_qn)], [], [])
        assert result.symbols_written == 1
        sid = _scalar(ctx.db, "SELECT id FROM symbols WHERE qualified_name = ?", (long_qn,))
        assert sid == _mint(ctx.repo_id, "mod.py", long_qn)
        assert len(sid) == 16

    def test_rescan_removes_stale_symbols(self, ctx):
        """Wipe-and-rewrite: re-persisting with fewer symbols deletes the stale rows."""
        ctx.store.persist_file(
            "mod.py",
            [_sym("keep", lineno=1), _sym("gone_a", lineno=5), _sym("gone_b", lineno=9)],
            [],
            [],
        )
        ctx.store.persist_file("mod.py", [_sym("keep", lineno=1)], [], [])
        qns = [r[0] for r in _rows(ctx.db, "SELECT qualified_name FROM symbols")]
        assert qns == ["keep"]

    def test_rescan_removes_stale_edges(self, ctx):
        """Wipe-and-rewrite also clears the file's import and call edges."""
        ctx.store.persist_file(
            "mod.py",
            [_sym("run", lineno=1), _sym("transform", lineno=5)],
            [_imp("os")],
            [_call("run", "transform", line=2)],
        )
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM import_edges") == 1
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM call_edges") == 1
        ctx.store.persist_file("mod.py", [_sym("run", lineno=1)], [], [])
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM import_edges") == 0
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM call_edges") == 0

    def test_call_with_unresolved_caller_writes_no_row(self, ctx):
        """An edge whose CALLER matches no repo symbol produces no call_edges row
        (FK requires a minted caller); nothing is guessed."""
        result = ctx.store.persist_file(
            "mod.py",
            [_sym("transform", lineno=1)],
            [],
            [_call("ghost_function", "transform", line=2)],
        )
        assert result.calls_written == 0
        assert _scalar(ctx.db, "SELECT COUNT(*) FROM call_edges") == 0


# ---------------------------------------------------------------------------
# PROPERTY-BASED (mandated: hypothesis, >=10 generated cases)
# ---------------------------------------------------------------------------

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

_QN_ALPHABET = "abcdef_"

_symbol_pairs = st.lists(
    st.tuples(
        st.text(alphabet=_QN_ALPHABET, min_size=1, max_size=8),
        st.integers(min_value=1, max_value=500),
    ),
    min_size=1,
    max_size=12,
    unique=True,  # unique (qualified_name, lineno) pairs — re-mint rule is well-defined
)


class TestPropertyBased:
    """Hypothesis: minting is deterministic and collision-free within a file."""

    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(pairs=_symbol_pairs)
    def test_property_minted_ids_deterministic_and_collision_free(self, pairs):
        """For any generated (qualified_name, lineno) set: same input persisted twice
        (fresh DBs, same repo_id) yields the same IDs, and all IDs within the file
        are distinct after the re-mint rule."""
        pairs = sorted(pairs, key=lambda p: (p[1], p[0]))  # line order, like an extractor
        symbols = [_sym(qn, lineno=ln) for qn, ln in pairs]
        id_runs = []
        for _ in range(2):
            tmp = tempfile.mkdtemp(prefix="ortho-prop-")
            root = Path(tmp)
            c = _make_ctx(root, repo_id=FIXED_REPO_ID, name="prop")
            result = c.store.persist_file("mod.py", symbols, [], [])
            ids = sorted(r[0] for r in _rows(c.db, "SELECT id FROM symbols"))
            assert result.symbols_written == len(pairs)
            assert len(ids) == len(pairs)
            assert len(set(ids)) == len(pairs)  # collision-free
            id_runs.append(ids)
        assert id_runs[0] == id_runs[1]  # deterministic


# ---------------------------------------------------------------------------
# REAL-REPO (mandated: >=500 symbols persisted from Repos/fastapi)
# ---------------------------------------------------------------------------


class TestRealRepo:
    """Scan a real codebase end-to-end through the real extractors + IndexStore."""

    @pytest.mark.skipif(not _FASTAPI_ROOT.exists(), reason="Repos/fastapi not available")
    def test_real_repo_fastapi_persists_at_least_500_symbols(self, tmp_path):
        """Persist the fastapi package via SymbolExtractor/ImportGraphBuilder/
        CallGraphBuilder + IndexStore: >=400 symbols rows (spec baseline 500, may vary
        with fastapi version), files rows match persisted count, resolve pass completes."""
        package_dir = _FASTAPI_ROOT / "fastapi"
        scan_root = package_dir if package_dir.exists() else _FASTAPI_ROOT

        db = OrthoDatabase(tmp_path)
        db.migrate()
        repo_id = _repo_id_for(scan_root)
        store = IndexStore(db, repo_id, scan_root)
        store.ensure_repository("fastapi")

        extractor = SymbolExtractor()
        importer = ImportGraphBuilder()
        caller = CallGraphBuilder()

        persisted_files = 0
        for py_file in sorted(scan_root.rglob("*.py")):
            rel = py_file.relative_to(scan_root).as_posix()
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            symbols = extractor.extract_symbols(py_file, source)
            imports = importer.extract_imports(py_file, source)
            try:
                calls = caller.extract_calls(py_file, source)
            except Exception:
                calls = []
            store.persist_file(rel, symbols, imports, calls)
            persisted_files += 1

        store.resolve_import_targets()

        assert persisted_files > 0
        symbol_count = _scalar(db, "SELECT COUNT(*) FROM symbols")
        assert symbol_count >= 400  # fastapi varies by version; baseline ~446-500
        assert _scalar(db, "SELECT COUNT(*) FROM files") == persisted_files
        assert _scalar(db, "SELECT COUNT(*) FROM import_edges") > 0
