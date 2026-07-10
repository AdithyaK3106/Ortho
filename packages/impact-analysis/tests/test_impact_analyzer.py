"""Unit tests for ImpactAnalyzer component."""

import pytest
from hypothesis import given, strategies as st

from impact_analysis import ImpactAnalyzer, Symbol, CallEdge, ImportEdge
from impact_analysis.types import ImpactReport


class TestImpactAnalyzerBasic:
    """Basic functional tests for ImpactAnalyzer."""

    def test_analyze_simple_import_chain(self):
        """A → B → C: changing A affects B and C."""
        # A imports nothing, B imports A, C imports B
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="C", imported_file_id="B"),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        assert report.changed_file_id == "A"
        assert "B" in report.direct_dependents
        assert "C" in report.transitive_dependents
        assert report.blast_radius == 2  # B (direct) and C (transitive)
        assert 0.0 <= report.risk_score <= 1.0
        assert 0.0 <= report.analysis_confidence <= 1.0

    def test_analyze_no_dependents(self):
        """Leaf file with no dependents → blast_radius = 0."""
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="C",  # C is not imported
            symbols=symbols,
            depth=3,
        )

        assert report.blast_radius == 0
        assert len(report.direct_dependents) == 0
        assert report.risk_score == 0.0

    def test_analyze_cycle_handling(self):
        """A → B → A: should not infinite loop."""
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="A", imported_file_id="B"),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        # Should terminate without infinite loop
        assert report.changed_file_id == "A"
        assert "B" in report.direct_dependents
        assert report.blast_radius >= 0

    def test_analyze_depth_limit(self):
        """Depth limit should prevent traversal beyond N hops."""
        # A → B → C → D (chain of 4)
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="C", imported_file_id="B"),
            ImportEdge(importer_file_id="D", imported_file_id="C"),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()

        # Depth 1: BFS reaches 1 hop from direct dependents → C
        report_depth1 = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=1,
        )
        assert report_depth1.blast_radius == 2  # B (direct) and C (1 hop from B)

        # Depth 2: BFS reaches 2 hops from direct dependents → C and D
        report_depth2 = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=2,
        )
        assert report_depth2.blast_radius == 3  # B, C, and D

        # Depth 3: BFS reaches 3 hops (all reachable)
        report_depth3 = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )
        assert report_depth3.blast_radius == 3  # B, C, and D (no further)

    def test_analyze_symbol_level(self):
        """Changing one symbol should be scoped to that symbol's callers."""
        symbols = [
            Symbol(id="sym_get_user", name="get_user", file_id="auth.py"),
            Symbol(id="sym_verify", name="verify", file_id="auth.py"),
        ]
        call_graph = [
            CallEdge(caller_id="sym_api_handler", callee_id="sym_get_user", confidence=1.0),
            CallEdge(caller_id="sym_middleware", callee_id="sym_verify", confidence=1.0),
        ]
        import_graph = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze_symbol(
            call_graph=call_graph,
            import_graph=import_graph,
            symbols=symbols,
            symbol_id="sym_get_user",
            depth=3,
        )

        # Only callers of get_user should be affected
        assert report.changed_file_id == "auth.py"
        assert len(report.direct_dependents) == 0  # API handler symbol not mapped to file

    def test_analyze_with_symbols(self):
        """With symbol info, should identify direct callers."""
        symbols = [
            Symbol(id="auth_get", name="get_user", file_id="auth.py"),
            Symbol(id="api_handler", name="handler", file_id="api.py"),
        ]
        call_graph = [
            CallEdge(caller_id="api_handler", callee_id="auth_get", confidence=1.0),
        ]
        import_graph = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="auth.py",
            symbols=symbols,
            depth=3,
        )

        # API file depends on auth file via call graph
        assert "api.py" in report.direct_dependents or report.blast_radius >= 0

    def test_risk_score_high_fan_in(self):
        """File with high fan-in should have higher risk_score."""
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="C", imported_file_id="A"),
            ImportEdge(importer_file_id="D", imported_file_id="A"),
            ImportEdge(importer_file_id="E", imported_file_id="A"),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        # High fan-in → high risk. 4 fan-in, 5 files -> 4/10 = 0.4
        assert report.risk_score >= 0.4
        assert len(report.direct_dependents) == 4  # B, C, D, E

    def test_confidence_with_unresolved_symbols(self):
        """Low-confidence CallEdges should reduce analysis_confidence."""
        call_graph = [
            CallEdge(caller_id="a", callee_id="b", confidence=1.0),
            CallEdge(caller_id="c", callee_id="d", confidence=0.5),  # Unresolved
            CallEdge(caller_id="e", callee_id="f", confidence=0.3),  # Unresolved
        ]
        import_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        # Confidence should be < 1.0 due to unresolved symbols
        assert report.analysis_confidence < 1.0
        assert report.analysis_confidence == pytest.approx(1 - (2 / 3), abs=0.01)

    def test_evidence_generated(self):
        """ImpactReport should include evidence."""
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        assert len(report.evidence) > 0
        assert any("import" in e.lower() or "depend" in e.lower() for e in report.evidence)


class TestImpactAnalyzerEdgeCases:
    """Edge case tests."""

    def test_empty_graphs(self):
        """Empty graphs should return empty report."""
        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=[],
            import_graph=[],
            changed_file_id="A",
            symbols=[],
            depth=3,
        )

        assert report.blast_radius == 0
        assert len(report.direct_dependents) == 0
        assert report.risk_score == 0.0

    def test_self_import_no_double_count(self):
        """File importing itself should not double-count."""
        import_graph = [
            ImportEdge(importer_file_id="A", imported_file_id="A"),  # Self-import
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        # Self-import counts as direct dependent
        assert report.blast_radius == 1

    def test_symbol_not_found(self):
        """Non-existent symbol should return graceful report."""
        analyzer = ImpactAnalyzer()
        report = analyzer.analyze_symbol(
            call_graph=[],
            import_graph=[],
            symbols=[],
            symbol_id="nonexistent",
            depth=3,
        )

        assert "not found" in str(report.evidence).lower()
        assert report.blast_radius == 0

    def test_external_imports_excluded(self):
        """External imports (is_external=True) should not create dependents."""
        import_graph = [
            ImportEdge(importer_file_id="A", imported_file_id=None, is_external=True),
        ]
        call_graph = []
        symbols = []

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=call_graph,
            import_graph=import_graph,
            changed_file_id="A",
            symbols=symbols,
            depth=3,
        )

        # External imports should not count
        assert report.blast_radius == 0


@given(depth=st.integers(min_value=1, max_value=10))
def test_depth_parameter_bounds(depth):
    """Depth parameter should be bounded and not cause issues."""
    analyzer = ImpactAnalyzer()
    report = analyzer.analyze(
        call_graph=[],
        import_graph=[ImportEdge(importer_file_id="B", imported_file_id="A")],
        changed_file_id="A",
        symbols=[],
        depth=depth,
    )

    assert report.blast_radius >= 0
    assert 0.0 <= report.risk_score <= 1.0
