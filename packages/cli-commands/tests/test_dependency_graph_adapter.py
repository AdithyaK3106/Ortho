"""Tests for DependencyGraphAdapter (task-017 spec.md Component 4)."""

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from repo_intelligence.import_graph import ImportEdge, ImportGraphBuilder

from cli_commands.dependency_graph_adapter import DependencyGraphAdapter

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "circular_import_fixture"


def _edge(target: str) -> ImportEdge:
    return ImportEdge(source_module="<current>", target_module=target, import_type="import", lineno=1)


class TestGetEdges:
    def test_no_edges(self) -> None:
        adapter = DependencyGraphAdapter({}, {})
        assert adapter.get_edges() == []

    def test_simple_acyclic_chain(self) -> None:
        import_edges_by_file = {
            "a.py": [_edge("b")],
            "b.py": [_edge("c")],
            "c.py": [],
        }
        file_to_module = {"a.py": "a", "b.py": "b", "c.py": "c"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        edges = adapter.get_edges()
        assert ("a", "b") in edges
        assert ("b", "c") in edges
        assert len(edges) == 2

    def test_unmapped_target_excluded(self) -> None:
        import_edges_by_file = {"a.py": [_edge("os")]}  # stdlib import, unresolvable
        file_to_module = {"a.py": "a"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        assert adapter.get_edges() == []

    def test_determinism(self) -> None:
        import_edges_by_file = {"a.py": [_edge("b")], "b.py": []}
        file_to_module = {"a.py": "a", "b.py": "b"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        first = adapter.get_edges()
        second = adapter.get_edges()
        assert first == second

    def test_large_acyclic_graph_completes(self) -> None:
        n = 50
        import_edges_by_file = {}
        file_to_module = {}
        for i in range(n):
            file_to_module[f"f{i}.py"] = f"m{i}"
            if i < n - 1:
                import_edges_by_file[f"f{i}.py"] = [_edge(f"m{i+1}")]
            else:
                import_edges_by_file[f"f{i}.py"] = []
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        edges = adapter.get_edges()
        assert len(edges) == n - 1
        assert adapter.find_cycles() == []


class TestFindCycles:
    def test_no_edges_no_cycles(self) -> None:
        adapter = DependencyGraphAdapter({}, {})
        assert adapter.find_cycles() == []

    def test_acyclic_chain_no_cycles(self) -> None:
        import_edges_by_file = {"a.py": [_edge("b")], "b.py": [_edge("c")], "c.py": []}
        file_to_module = {"a.py": "a", "b.py": "b", "c.py": "c"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        assert adapter.find_cycles() == []

    def test_direct_2_cycle(self) -> None:
        import_edges_by_file = {"a.py": [_edge("b")], "b.py": [_edge("a")]}
        file_to_module = {"a.py": "a", "b.py": "b"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        cycles = adapter.find_cycles()
        assert len(cycles) == 1
        assert set(cycles[0]) == {"a", "b"}

    def test_3_node_cycle(self) -> None:
        import_edges_by_file = {
            "a.py": [_edge("b")],
            "b.py": [_edge("c")],
            "c.py": [_edge("a")],
        }
        file_to_module = {"a.py": "a", "b.py": "b", "c.py": "c"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        cycles = adapter.find_cycles()
        assert len(cycles) == 1
        assert set(cycles[0]) == {"a", "b", "c"}

    def test_two_independent_cycles(self) -> None:
        import_edges_by_file = {
            "a.py": [_edge("b")],
            "b.py": [_edge("a")],
            "c.py": [_edge("d")],
            "d.py": [_edge("c")],
        }
        file_to_module = {"a.py": "a", "b.py": "b", "c.py": "c", "d.py": "d"}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        cycles = adapter.find_cycles()
        assert len(cycles) == 2

    def test_empty_import_edges_by_file(self) -> None:
        adapter = DependencyGraphAdapter({}, {"a.py": "a"})
        assert adapter.find_cycles() == []

    def test_real_repo_scan_completes_bounded_time(self) -> None:
        """Real-repo scan test (mandatory per spec.md): must complete <30s."""
        import time

        repo_root = Path(__file__).resolve().parents[3] / "repos" / "click" / "src" / "click"
        builder = ImportGraphBuilder()
        import_edges_by_file: dict[str, list[ImportEdge]] = {}
        file_to_module: dict[str, str] = {}
        for py_file in repo_root.glob("*.py"):
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            import_edges_by_file[str(py_file)] = builder.extract_imports(py_file, source)
            file_to_module[str(py_file)] = py_file.stem

        t0 = time.time()
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        cycles = adapter.find_cycles()
        elapsed = time.time() - t0

        assert elapsed < 30.0
        assert isinstance(cycles, list)

    def test_real_repo_with_known_circular_import(self) -> None:
        """Real-repo cycle detection against a genuine hand-verified circular
        import fixture package (module_a <-> module_b), per spec.md's
        BUILDER/TEST-DESIGNER-authorized fixture."""
        builder = ImportGraphBuilder()
        import_edges_by_file: dict[str, list[ImportEdge]] = {}
        file_to_module: dict[str, str] = {}
        for py_file in _FIXTURE_DIR.glob("*.py"):
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            import_edges_by_file[str(py_file)] = builder.extract_imports(py_file, source)
            file_to_module[str(py_file)] = py_file.stem

        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        cycles = adapter.find_cycles()
        assert len(cycles) >= 1
        assert any(set(c) == {"module_a", "module_b"} for c in cycles)


# --- Property-based test (spec.md requires >=1, hypothesis, >=10 generated cases) ---

_module_names = st.text(alphabet=st.characters(whitelist_categories=["Ll"]), min_size=1, max_size=5)


class TestFindCyclesProperty:
    @given(pair=st.lists(_module_names, min_size=2, max_size=2, unique=True))
    @settings(max_examples=15)
    def test_reverse_edge_between_connected_nodes_creates_cycle(self, pair: list[str]) -> None:
        """Property: given A->B (acyclic), adding B->A always creates >=1 cycle."""
        a, b = pair
        import_edges_by_file = {f"{a}.py": [_edge(b)], f"{b}.py": [_edge(a)]}
        file_to_module = {f"{a}.py": a, f"{b}.py": b}
        adapter = DependencyGraphAdapter(import_edges_by_file, file_to_module)
        cycles = adapter.find_cycles()
        assert len(cycles) >= 1
