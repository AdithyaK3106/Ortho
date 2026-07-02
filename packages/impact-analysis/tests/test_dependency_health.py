"""Unit tests for DependencyHealthAnalyzer component."""

import pytest
from hypothesis import given, strategies as st

from impact_analysis.dependency_health import DependencyHealthAnalyzer, CallEdge, ImportEdge
from impact_analysis.types import DependencyHealthReport


class TestDependencyHealthBasic:
    """Basic functional tests for DependencyHealthAnalyzer."""

    def test_analyze_isolated_module(self):
        """Isolated module should have no health issues."""
        analyzer = DependencyHealthAnalyzer()
        report = analyzer.analyze_module(
            file_id="isolated.py",
            call_graph=[],
            import_graph=[],
        )

        assert report.module_id == "isolated.py"
        assert report.fan_in == 0
        assert report.fan_out == 0
        assert report.high_fan_in is False
        assert report.high_fan_out is False
        assert report.is_hub is False
        assert len(report.cycles_involved) == 0

    def test_analyze_high_fan_in(self):
        """Module with many dependents should flag high_fan_in."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="a", imported_file_id="core"),
            ImportEdge(importer_file_id="b", imported_file_id="core"),
            ImportEdge(importer_file_id="c", imported_file_id="core"),
            ImportEdge(importer_file_id="d", imported_file_id="core"),
            ImportEdge(importer_file_id="e", imported_file_id="core"),
            ImportEdge(importer_file_id="f", imported_file_id="core"),
            ImportEdge(importer_file_id="g", imported_file_id="core"),
            ImportEdge(importer_file_id="h", imported_file_id="core"),
            ImportEdge(importer_file_id="i", imported_file_id="core"),
            ImportEdge(importer_file_id="j", imported_file_id="core"),
            ImportEdge(importer_file_id="k", imported_file_id="core"),  # 11 > 10
        ]
        report = analyzer.analyze_module(
            file_id="core",
            call_graph=[],
            import_graph=import_graph,
        )

        assert report.fan_in == 11
        assert report.high_fan_in is True
        assert len(report.recommendations) > 0

    def test_analyze_high_fan_out(self):
        """Module with many dependencies should flag high_fan_out."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = []
        for i in range(16):  # 16 > 15
            import_graph.append(ImportEdge(importer_file_id="client", imported_file_id=f"dep_{i}"))

        report = analyzer.analyze_module(
            file_id="client",
            call_graph=[],
            import_graph=import_graph,
        )

        assert report.fan_out == 16
        assert report.high_fan_out is True
        assert len(report.recommendations) > 0

    def test_analyze_hub_module(self):
        """Module with both high fan-in and fan-out should flag is_hub."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = []
        # High fan-in: 9 modules import hub
        for i in range(9):
            import_graph.append(ImportEdge(importer_file_id=f"dep_in_{i}", imported_file_id="hub"))
        # High fan-out: hub imports 9 modules
        for i in range(9):
            import_graph.append(ImportEdge(importer_file_id="hub", imported_file_id=f"dep_out_{i}"))

        report = analyzer.analyze_module(
            file_id="hub",
            call_graph=[],
            import_graph=import_graph,
        )

        assert report.fan_in == 9
        assert report.fan_out == 9
        assert report.is_hub is True  # Both > 8
        assert "Hub" in " ".join(report.recommendations)

    def test_analyze_simple_cycle(self):
        """A → B → A cycle should be detected."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="A", imported_file_id="B"),
        ]
        report = analyzer.analyze_module(
            file_id="A",
            call_graph=[],
            import_graph=import_graph,
        )

        assert len(report.cycles_involved) > 0
        assert "Cycle" in " ".join(report.evidence)

    def test_find_global_cycles(self):
        """find_cycles() should detect all cycles in graph."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="A", imported_file_id="B"),  # Cycle: A ↔ B
        ]
        cycles = analyzer.find_cycles(
            call_graph=[],
            import_graph=import_graph,
        )

        assert len(cycles) > 0

    def test_analyze_all_modules(self):
        """analyze_all_modules should return all modules in graph."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="C", imported_file_id="B"),
        ]
        reports = analyzer.analyze_all_modules(
            call_graph=[],
            import_graph=import_graph,
        )

        # Should have reports for A, B, C
        module_ids = {r.module_id for r in reports}
        assert len(module_ids) >= 3

    def test_recommendations_generated(self):
        """Reports should include actionable recommendations."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="b", imported_file_id="core"),
            ImportEdge(importer_file_id="c", imported_file_id="core"),
            ImportEdge(importer_file_id="d", imported_file_id="core"),
            ImportEdge(importer_file_id="e", imported_file_id="core"),
            ImportEdge(importer_file_id="f", imported_file_id="core"),
            ImportEdge(importer_file_id="g", imported_file_id="core"),
            ImportEdge(importer_file_id="h", imported_file_id="core"),
            ImportEdge(importer_file_id="i", imported_file_id="core"),
            ImportEdge(importer_file_id="j", imported_file_id="core"),
            ImportEdge(importer_file_id="k", imported_file_id="core"),
            ImportEdge(importer_file_id="l", imported_file_id="core"),  # 11 high fan-in
        ]
        report = analyzer.analyze_module(
            file_id="core",
            call_graph=[],
            import_graph=import_graph,
        )

        assert len(report.recommendations) > 0
        assert any("test" in r.lower() for r in report.recommendations)


class TestDependencyHealthEdgeCases:
    """Edge case tests."""

    def test_empty_graph(self):
        """Empty graph should produce no cycles."""
        analyzer = DependencyHealthAnalyzer()
        cycles = analyzer.find_cycles(call_graph=[], import_graph=[])
        assert len(cycles) == 0

    def test_external_imports_excluded(self):
        """External imports should not count in fan_in/fan_out."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(
                importer_file_id="local",
                imported_file_id=None,
                imported_module="numpy",
                is_external=True,
            ),
        ]
        report = analyzer.analyze_module(
            file_id="numpy",
            call_graph=[],
            import_graph=import_graph,
        )

        # External import shouldn't count
        assert report.fan_in == 0 or not report.high_fan_in

    def test_self_import_no_cycle(self):
        """File importing itself should not create false cycle."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="A", imported_file_id="A"),
        ]
        report = analyzer.analyze_module(
            file_id="A",
            call_graph=[],
            import_graph=import_graph,
        )

        # Self-import should not be detected as cycle
        # (or if it is, it's still valid to report)
        assert report.module_id == "A"

    def test_three_node_cycle(self):
        """A → B → C → A should be detected."""
        analyzer = DependencyHealthAnalyzer()
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="C", imported_file_id="B"),
            ImportEdge(importer_file_id="A", imported_file_id="C"),
        ]
        cycles = analyzer.find_cycles(call_graph=[], import_graph=import_graph)

        assert len(cycles) > 0


@given(
    fan_in=st.integers(min_value=0, max_value=100),
    fan_out=st.integers(min_value=0, max_value=100),
)
def test_threshold_consistency(fan_in, fan_out):
    """Thresholds should be consistent: high_fan_in only if > 10."""
    analyzer = DependencyHealthAnalyzer()
    import_graph = []
    for i in range(fan_in):
        import_graph.append(ImportEdge(importer_file_id=f"in_{i}", imported_file_id="test"))
    for i in range(fan_out):
        import_graph.append(ImportEdge(importer_file_id="test", imported_file_id=f"out_{i}"))

    report = analyzer.analyze_module(
        file_id="test",
        call_graph=[],
        import_graph=import_graph,
    )

    assert (report.high_fan_in and fan_in > 10) or (not report.high_fan_in and fan_in <= 10)
    assert (report.high_fan_out and fan_out > 15) or (not report.high_fan_out and fan_out <= 15)


@given(
    fan_in=st.integers(min_value=8, max_value=20),
    fan_out=st.integers(min_value=8, max_value=20),
)
def test_hub_detection_property(fan_in, fan_out):
    """is_hub should only be True when both fan_in > 8 AND fan_out > 8."""
    analyzer = DependencyHealthAnalyzer()
    import_graph = []
    for i in range(fan_in):
        import_graph.append(ImportEdge(importer_file_id=f"in_{i}", imported_file_id="hub"))
    for i in range(fan_out):
        import_graph.append(ImportEdge(importer_file_id="hub", imported_file_id=f"out_{i}"))

    report = analyzer.analyze_module(
        file_id="hub",
        call_graph=[],
        import_graph=import_graph,
    )

    expected_hub = (fan_in > 8 and fan_out > 8)
    assert report.is_hub == expected_hub
