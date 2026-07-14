"""Tests for RepoGraphQueries, SymbolIndex, CodeMetricsAdapter (task-017 spec.md
Components 1, 2, 5). Written fresh against spec.md's contracts, independent of
implementation details."""

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from repo_intelligence.call_graph import CallEdge, CallGraphBuilder
from repo_intelligence.graph_queries import CodeMetricsAdapter, RepoGraphQueries, SymbolIndex
from repo_intelligence.import_graph import ImportEdge, ImportGraphBuilder
from repo_intelligence.symbol_extractor import Symbol, SymbolExtractor

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CLICK_ROOT = _REPO_ROOT / "repos" / "click" / "src" / "click"
_FLASK_ROOT = _REPO_ROOT / "repos" / "flask" / "src" / "flask"


def _edge(caller: str, callee: str, distance: int = 1) -> CallEdge:
    return CallEdge(
        caller_id=caller,
        caller_name=caller,
        callee_id=callee,
        callee_name=callee,
        call_site_line=1,
        confidence=1.0,
    )


class TestFindCallers:
    def test_direct_caller_found(self) -> None:
        queries = RepoGraphQueries([_edge("A", "target")], {})
        assert queries.find_callers("target", depth=1) == ["A"]

    def test_no_callers(self) -> None:
        queries = RepoGraphQueries([_edge("A", "B")], {})
        assert queries.find_callers("nonexistent", depth=1) == []

    def test_transitive_depth_2(self) -> None:
        # A calls B calls target
        edges = [_edge("A", "B"), _edge("B", "target")]
        queries = RepoGraphQueries(edges, {})
        assert queries.find_callers("target", depth=1) == ["B"]
        assert sorted(queries.find_callers("target", depth=2)) == ["A", "B"]

    def test_recursive_function_terminates(self) -> None:
        edges = [_edge("A", "A")]
        queries = RepoGraphQueries(edges, {})
        result = queries.find_callers("A", depth=5)
        assert isinstance(result, list)

    def test_duplicate_edges_deduped(self) -> None:
        edges = [_edge("A", "target"), _edge("A", "target")]
        queries = RepoGraphQueries(edges, {})
        assert queries.find_callers("target", depth=1) == ["A"]

    def test_symbol_not_found(self) -> None:
        queries = RepoGraphQueries([], {})
        assert queries.find_callers("unknown_symbol", depth=1) == []

    def test_empty_call_edges(self) -> None:
        queries = RepoGraphQueries([], {})
        assert queries.find_callers("anything", depth=3) == []

    def test_depth_zero_returns_empty(self) -> None:
        queries = RepoGraphQueries([_edge("A", "target")], {})
        assert queries.find_callers("target", depth=0) == []

    def test_real_repo_scan_no_crash(self) -> None:
        """Real-repo scan test (mandatory per spec.md)."""
        builder = CallGraphBuilder()
        core_file = _CLICK_ROOT / "core.py"
        source = core_file.read_text(encoding="utf-8", errors="ignore")
        edges = builder.extract_calls(core_file, source)
        queries = RepoGraphQueries(edges, {})
        result = queries.find_callers("Command", depth=2)
        assert isinstance(result, list)


class TestFindImporters:
    def test_direct_importer_found(self) -> None:
        edges_by_file = {"importer.py": [ImportEdge("<current>", "target", "import", 1)]}
        queries = RepoGraphQueries([], edges_by_file)
        result = queries.find_importers("target.py", include_type=False)
        assert "importer.py" in result

    def test_include_type_true(self) -> None:
        edges_by_file = {"importer.py": [ImportEdge("<current>", "target", "import", 1)]}
        queries = RepoGraphQueries([], edges_by_file)
        result = queries.find_importers("target.py", include_type=True)
        assert result == [("importer.py", "import")]

    def test_no_importers(self) -> None:
        edges_by_file = {"other.py": [ImportEdge("<current>", "unrelated", "import", 1)]}
        queries = RepoGraphQueries([], edges_by_file)
        assert queries.find_importers("target.py", include_type=False) == []

    def test_empty_import_edges_by_file(self) -> None:
        queries = RepoGraphQueries([], {})
        assert queries.find_importers("anything.py") == []

    def test_from_import_type_preserved(self) -> None:
        edges_by_file = {"importer.py": [ImportEdge("<current>", "target", "from", 1)]}
        queries = RepoGraphQueries([], edges_by_file)
        result = queries.find_importers("target.py", include_type=True)
        assert result == [("importer.py", "from")]

    def test_relative_import_type_preserved(self) -> None:
        edges_by_file = {"importer.py": [ImportEdge("<current>", "target", "relative", 1)]}
        queries = RepoGraphQueries([], edges_by_file)
        result = queries.find_importers("target.py", include_type=True)
        assert result == [("importer.py", "relative")]

    def test_self_import_excluded(self) -> None:
        edges_by_file = {"target.py": [ImportEdge("<current>", "target", "import", 1)]}
        queries = RepoGraphQueries([], edges_by_file)
        result = queries.find_importers("target.py", include_type=False)
        assert "target.py" not in result

    def test_real_repo_scan_no_crash(self) -> None:
        """Real-repo scan test (mandatory per spec.md)."""
        builder = ImportGraphBuilder()
        edges_by_file: dict[str, list[ImportEdge]] = {}
        for py_file in list(_FLASK_ROOT.glob("*.py"))[:10]:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            edges_by_file[str(py_file)] = builder.extract_imports(py_file, source)
        queries = RepoGraphQueries([], edges_by_file)
        result = queries.find_importers(str(_FLASK_ROOT / "app.py"), include_type=True)
        assert isinstance(result, list)


class TestSymbolIndex:
    def test_known_file_symbols_present(self) -> None:
        symbols = [
            Symbol(name="foo", qualified_name="foo", type="function", lineno=1),
            Symbol(name="bar", qualified_name="bar", type="function", lineno=5),
            Symbol(name="Baz", qualified_name="Baz", type="class", lineno=10),
        ]
        index = SymbolIndex({"file.py": symbols})
        assert index.symbols_in_file("file.py") == ["foo", "bar", "Baz"]

    def test_unknown_file(self) -> None:
        index = SymbolIndex({"file.py": []})
        assert index.symbols_in_file("other.py") == []

    def test_empty_symbols_list_for_file(self) -> None:
        index = SymbolIndex({"file.py": []})
        assert index.symbols_in_file("file.py") == []

    def test_duplicate_names_both_returned(self) -> None:
        symbols = [
            Symbol(name="method", qualified_name="A.method", type="method", lineno=1),
            Symbol(name="method", qualified_name="B.method", type="method", lineno=2),
        ]
        index = SymbolIndex({"file.py": symbols})
        assert index.symbols_in_file("file.py") == ["method", "method"]

    def test_empty_dict(self) -> None:
        index = SymbolIndex({})
        assert index.symbols_in_file("anything.py") == []

    def test_real_repo_scan_no_crash(self) -> None:
        """Real-repo scan test (mandatory per spec.md)."""
        extractor = SymbolExtractor()
        app_file = _FLASK_ROOT / "app.py"
        source = app_file.read_text(encoding="utf-8", errors="ignore")
        symbols = extractor.extract_symbols(app_file, source)
        index = SymbolIndex({str(app_file): symbols})
        result = index.symbols_in_file(str(app_file))
        assert isinstance(result, list)
        assert len(result) > 0


class TestCodeMetricsAdapter:
    def test_real_file_known_line_count(self, tmp_path: Path) -> None:
        fixture = tmp_path / "fixture.py"
        fixture.write_text("line1\nline2\nline3\n", encoding="utf-8")
        adapter = CodeMetricsAdapter({str(fixture): "mymodule"})
        assert adapter.get_module_lines("mymodule") == 3

    def test_unknown_module(self) -> None:
        adapter = CodeMetricsAdapter({})
        assert adapter.get_module_lines("unknown") == 0
        assert adapter.get_module_functions("unknown") == 0

    def test_missing_file_on_disk(self) -> None:
        adapter = CodeMetricsAdapter({"/definitely/not/real/path.py": "mymodule"})
        assert adapter.get_module_lines("mymodule") == 0
        assert adapter.get_module_functions("mymodule") == 0

    def test_empty_file(self, tmp_path: Path) -> None:
        fixture = tmp_path / "empty.py"
        fixture.write_text("", encoding="utf-8")
        adapter = CodeMetricsAdapter({str(fixture): "mymodule"})
        assert adapter.get_module_lines("mymodule") == 0

    def test_function_count_known_file(self, tmp_path: Path) -> None:
        fixture = tmp_path / "funcs.py"
        fixture.write_text(
            "def a():\n    pass\n\ndef b():\n    pass\n\ndef c():\n    pass\n",
            encoding="utf-8",
        )
        adapter = CodeMetricsAdapter({str(fixture): "mymodule"})
        assert adapter.get_module_functions("mymodule") == 3

    def test_function_count_with_class_methods(self, tmp_path: Path) -> None:
        fixture = tmp_path / "cls.py"
        fixture.write_text(
            "class Foo:\n    def method_a(self):\n        pass\n    def method_b(self):\n        pass\n",
            encoding="utf-8",
        )
        adapter = CodeMetricsAdapter({str(fixture): "mymodule"})
        assert adapter.get_module_functions("mymodule") == 2

    def test_nested_functions_both_counted(self, tmp_path: Path) -> None:
        fixture = tmp_path / "nested.py"
        fixture.write_text(
            "def outer():\n    def inner():\n        pass\n    return inner\n",
            encoding="utf-8",
        )
        adapter = CodeMetricsAdapter({str(fixture): "mymodule"})
        assert adapter.get_module_functions("mymodule") == 2

    def test_syntax_error_in_file(self, tmp_path: Path) -> None:
        fixture = tmp_path / "broken.py"
        fixture.write_text("def broken(:\n    pass\n", encoding="utf-8")
        adapter = CodeMetricsAdapter({str(fixture): "mymodule"})
        assert adapter.get_module_functions("mymodule") == 0

    def test_multiple_files_same_module_summed(self, tmp_path: Path) -> None:
        f1 = tmp_path / "f1.py"
        f2 = tmp_path / "f2.py"
        f1.write_text("def a():\n    pass\n", encoding="utf-8")
        f2.write_text("def b():\n    pass\n", encoding="utf-8")
        adapter = CodeMetricsAdapter({str(f1): "mymodule", str(f2): "mymodule"})
        assert adapter.get_module_functions("mymodule") == 2

    def test_real_repo_scan_no_crash(self) -> None:
        """Real-repo scan test (mandatory per spec.md)."""
        models_file = _REPO_ROOT / "repos" / "requests" / "src" / "requests" / "models.py"
        adapter = CodeMetricsAdapter({str(models_file): "requests.models"})
        assert adapter.get_module_lines("requests.models") > 0
        assert adapter.get_module_functions("requests.models") > 0


# --- Property-based test (spec.md requires >=1, hypothesis, >=10 generated cases) ---

_symbol_names = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), min_size=1, max_size=10)


class TestFindCallersProperty:
    @given(names=st.lists(_symbol_names, min_size=1, max_size=6, unique=True))
    @settings(max_examples=25)
    def test_depth_n_plus_1_is_superset_of_depth_n(self, names: list[str]) -> None:
        """Property: increasing depth never loses previously-found callers."""
        # build a simple call chain: names[0] -> names[1] -> ... -> "target"
        edges = []
        chain = names + ["target"]
        for i in range(len(chain) - 1):
            edges.append(_edge(chain[i], chain[i + 1]))

        queries = RepoGraphQueries(edges, {})
        depth_n = set(queries.find_callers("target", depth=len(chain)))
        depth_n_plus_1 = set(queries.find_callers("target", depth=len(chain) + 1))
        assert depth_n.issubset(depth_n_plus_1)
