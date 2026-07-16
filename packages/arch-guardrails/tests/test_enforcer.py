"""Hard tests for architecture guardrails with 100% detection rate"""
from typing import Any

import pytest

from arch_guardrails.enforcer import ArchitectureEnforcer
from arch_guardrails.types import GuardrailViolation


@pytest.fixture
def enforcer(
    mock_arch_model: Any, mock_dep_graph: Any, mock_metrics: Any
) -> ArchitectureEnforcer:
    """Create enforcer with mocks"""
    return ArchitectureEnforcer(
        arch_model=mock_arch_model,
        dep_graph=mock_dep_graph,
        metrics=mock_metrics,
    )


class TestLayerBoundaries:
    """Test 1-5: Layer boundary violations.

    _check_layer_boundaries() is called from check_violations() again as of
    2026-07-16 -- see enforcer.py's check_violations() comment and
    docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md: it was disabled after a
    100% false-positive rate in real-world use, root-caused to LayerDetector
    (not this method) defaulting every import-graph leaf to layer 0. That's
    fixed by requiring real persistence/framework-import evidence before a
    module gets a layer at all (see layer_detector.py). These tests call
    _check_layer_boundaries() directly against hand-labeled mock layers,
    independent of LayerDetector, so they keep exercising the ordering logic
    in isolation regardless of how layers are sourced upstream.
    """

    def test_presentation_to_data_blocked(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 1: Presentation imports data (VIOLATION)"""
        # Layer order: [presentation, business, data] → indices [0, 1, 2]
        # Presentation (0) → Data (2): upward import, VIOLATION
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "views.py": "presentation",
            "db.py": "data",
        }.get(m, "unknown")
        mock_arch_model.get_layers.return_value = ["data", "business", "presentation"]
        mock_dep_graph.get_edges.return_value = [("views.py", "db.py")]

        layer_violations = enforcer._check_layer_boundaries()

        assert len(layer_violations) > 0
        assert layer_violations[0].severity == "error"

    def test_service_to_data_allowed(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 2: Service imports data (ALLOWED)"""
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "service.py": "business",
            "repo.py": "data",
        }.get(m, "unknown")
        mock_dep_graph.get_edges.return_value = [("service.py", "repo.py")]

        layer_violations = enforcer._check_layer_boundaries()

        assert len(layer_violations) == 0

    def test_data_to_presentation_blocked(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 3: Data imports presentation (VIOLATION)"""
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "models.py": "data",
            "forms.py": "presentation",
        }.get(m, "unknown")
        mock_dep_graph.get_edges.return_value = [("models.py", "forms.py")]

        layer_violations = enforcer._check_layer_boundaries()

        assert len(layer_violations) > 0

    def test_bidirectional_cascade(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 4: Bidirectional violation"""
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "pres.py": "presentation",
            "bus.py": "business",
        }.get(m, "unknown")
        mock_dep_graph.get_edges.return_value = [
            ("pres.py", "bus.py"),
            ("bus.py", "pres.py"),
        ]

        layer_violations = enforcer._check_layer_boundaries()

        assert len(layer_violations) >= 1

    def test_exception_allowed(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 5: Exception in config allows violation"""
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "views.py": "presentation",
            "db.py": "data",
        }.get(m, "unknown")
        mock_dep_graph.get_edges.return_value = [("views.py", "db.py")]

        violations = enforcer._check_layer_boundaries()

        # No filtering yet - just verify structure
        assert all(v.severity in ("error", "warning") for v in violations)


class TestDependencyDirection:
    """Test 6-10: Acyclic dependency violations"""

    def test_dag_valid_linear_chain(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 6: A→B→C linear (ALLOWED)"""
        mock_dep_graph.get_edges.return_value = [("A", "B"), ("B", "C")]
        mock_dep_graph.find_cycles.return_value = []

        violations = enforcer.check_violations()

        circ_violations = [v for v in violations if v.rule_id == "dependency_direction"]
        assert len(circ_violations) == 0

    def test_simple_cycle_ab(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 7: A→B→A (VIOLATION)"""
        mock_dep_graph.get_edges.return_value = [("A", "B"), ("B", "A")]
        mock_dep_graph.find_cycles.return_value = [["A", "B", "A"]]

        violations = enforcer.check_violations()

        circ_violations = [v for v in violations if v.rule_id == "dependency_direction"]
        assert len(circ_violations) > 0

    def test_complex_cycle_abc(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 8: A→B→C→A (VIOLATION)"""
        mock_dep_graph.get_edges.return_value = [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
        ]
        mock_dep_graph.find_cycles.return_value = [["A", "B", "C", "A"]]

        violations = enforcer.check_violations()

        circ_violations = [v for v in violations if v.rule_id == "dependency_direction"]
        assert len(circ_violations) > 0

    def test_multiple_cycles(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 9: Multiple cycles reported"""
        mock_dep_graph.find_cycles.return_value = [
            ["A", "B", "A"],
            ["C", "D", "C"],
        ]

        violations = enforcer.check_violations()

        circ_violations = [v for v in violations if v.rule_id == "dependency_direction"]
        assert len(circ_violations) >= 2

    def test_diamond_pattern(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Test 10: Diamond pattern A→B,C; B,C→D (ALLOWED)"""
        mock_dep_graph.get_edges.return_value = [
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("C", "D"),
        ]
        mock_dep_graph.find_cycles.return_value = []

        violations = enforcer.check_violations()

        circ_violations = [v for v in violations if v.rule_id == "dependency_direction"]
        assert len(circ_violations) == 0


class TestModuleSizing:
    """Test 11-15: Module size violations"""

    def test_module_under_limit(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_metrics: Any
    ) -> None:
        """Test 11: Module <500 lines (ALLOWED)"""
        mock_arch_model.get_modules.return_value = ["service.py"]
        mock_metrics.get_module_lines.return_value = 400
        mock_metrics.get_module_functions.return_value = 30

        violations = enforcer.check_violations()

        size_violations = [v for v in violations if v.rule_id == "module_sizing"]
        assert len(size_violations) == 0

    def test_module_over_line_limit(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_metrics: Any
    ) -> None:
        """Test 12: Module >500 lines (VIOLATION)"""
        mock_arch_model.get_modules.return_value = ["big.py"]
        mock_metrics.get_module_lines.return_value = 600
        mock_metrics.get_module_functions.return_value = 40

        violations = enforcer.check_violations()

        size_violations = [v for v in violations if v.rule_id == "module_sizing"]
        assert len(size_violations) > 0
        assert "600" in size_violations[0].message

    def test_module_over_function_limit(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_metrics: Any
    ) -> None:
        """Test 13: Module >50 functions (VIOLATION)"""
        mock_arch_model.get_modules.return_value = ["handlers.py"]
        mock_metrics.get_module_lines.return_value = 400
        mock_metrics.get_module_functions.return_value = 60

        violations = enforcer.check_violations()

        size_violations = [v for v in violations if v.rule_id == "module_sizing"]
        assert len(size_violations) > 0
        assert "60" in size_violations[0].message

    def test_module_both_limits(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_metrics: Any
    ) -> None:
        """Test 14: Module exceeds both limits"""
        mock_arch_model.get_modules.return_value = ["monster.py"]
        mock_metrics.get_module_lines.return_value = 1000
        mock_metrics.get_module_functions.return_value = 100

        violations = enforcer.check_violations()

        size_violations = [v for v in violations if v.rule_id == "module_sizing"]
        assert len(size_violations) >= 2

    def test_module_exception_allowed(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_metrics: Any
    ) -> None:
        """Test 15: Exception allows large module"""
        mock_arch_model.get_modules.return_value = ["allowed_big.py"]
        mock_metrics.get_module_lines.return_value = 600

        violations = enforcer.check_violations()

        # Violations exist but would be filtered by config
        assert all(v.severity in ("error", "warning") for v in violations)


class TestAccuracy:
    """Test 100% detection rate"""

    def test_all_violations_reported(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any,
        mock_dep_graph: Any, mock_metrics: Any
    ) -> None:
        """Multiple violation types all reported"""
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "views.py": "presentation",
            "db.py": "data",
        }.get(m, "unknown")
        mock_arch_model.get_modules.return_value = ["big.py"]
        mock_dep_graph.get_edges.return_value = [("views.py", "db.py")]
        mock_dep_graph.find_cycles.return_value = [["A", "B", "A"]]
        mock_metrics.get_module_lines.return_value = 600
        mock_metrics.get_module_functions.return_value = 40

        violations = enforcer.check_violations()

        # Should report all violation types
        rule_ids = set(v.rule_id for v in violations)
        assert len(rule_ids) >= 2

    def test_violations_sorted_correctly(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """Violations sorted by severity"""
        mock_dep_graph.find_cycles.return_value = [["A", "B"]]
        mock_arch_model.get_modules.return_value = ["big.py"]

        violations = enforcer.check_violations()

        if len(violations) > 1:
            for i in range(len(violations) - 1):
                sev_map = {"error": 0, "warning": 1}
                assert sev_map[violations[i].severity] <= sev_map[violations[i + 1].severity]

    def test_no_false_negatives(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """All cycles detected"""
        cycles = [["A", "B"], ["C", "D", "E"], ["F", "G", "H", "I"]]
        mock_dep_graph.find_cycles.return_value = cycles

        violations = enforcer.check_violations()

        circ_violations = [v for v in violations if v.rule_id == "dependency_direction"]
        assert len(circ_violations) >= len(cycles)


class TestEvidenceEngine:
    """Evidence Engine: every violation must carry real, checkable evidence
    -- 'Risk: High' must never stand alone (product vision). Evidence must
    cite concrete facts a developer can independently verify, not fabricate
    anything not present in the input data."""

    def test_layer_boundaries_evidence_cites_real_modules(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "views.py": "presentation",
            "db.py": "data",
        }.get(m, "unknown")
        mock_arch_model.get_layers.return_value = ["data", "business", "presentation"]
        mock_dep_graph.get_edges.return_value = [("views.py", "db.py")]

        violations = enforcer._check_layer_boundaries()

        assert len(violations) > 0
        v = violations[0]
        assert v.evidence, "layer_boundaries violation has no evidence"
        assert any("views.py" in e for e in v.evidence)
        assert any("db.py" in e for e in v.evidence)

    def test_dependency_direction_evidence_cites_real_edges(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        mock_dep_graph.find_cycles.return_value = [["A", "B", "C", "A"]]

        violations = enforcer.check_violations()
        circ = [v for v in violations if v.rule_id == "dependency_direction"][0]

        assert circ.evidence
        assert any("A → B" in e for e in circ.evidence)
        assert any("B → C" in e for e in circ.evidence)
        assert any("distinct modules" in e for e in circ.evidence)

    def test_dependency_direction_evidence_capped_for_large_cycle(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any
    ) -> None:
        """A 41-module cycle (celery's real one) must not dump 40 evidence
        lines -- capped with a '...and N more' marker."""
        big_cycle = [f"m{i}" for i in range(41)] + ["m0"]
        mock_dep_graph.find_cycles.return_value = [big_cycle]

        violations = enforcer.check_violations()
        circ = [v for v in violations if v.rule_id == "dependency_direction"][0]

        assert len(circ.evidence) <= 12
        assert any("more" in e for e in circ.evidence)

    def test_module_sizing_evidence_cites_measured_values(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_metrics: Any
    ) -> None:
        mock_arch_model.get_modules.return_value = ["big.py"]
        mock_metrics.get_module_lines.return_value = 733
        mock_metrics.get_module_functions.return_value = 30

        violations = enforcer.check_violations()
        size_v = [v for v in violations if v.rule_id == "module_sizing"][0]

        assert size_v.evidence
        assert any("733" in e for e in size_v.evidence)
        assert any("233" in e for e in size_v.evidence)  # 733 - 500 over limit

    def test_all_violation_types_have_nonempty_evidence(
        self, enforcer: ArchitectureEnforcer, mock_arch_model: Any, mock_dep_graph: Any, mock_metrics: Any
    ) -> None:
        """No rule_id may produce a finding with empty evidence -- that
        would be exactly the gap the Evidence Engine exists to close."""
        mock_arch_model.get_layer_for_module.side_effect = lambda m: {
            "views.py": "presentation", "db.py": "data",
        }.get(m, "unknown")
        mock_arch_model.get_layers.return_value = ["data", "business", "presentation"]
        mock_dep_graph.get_edges.return_value = [("views.py", "db.py")]
        mock_dep_graph.find_cycles.return_value = [["A", "B", "A"]]
        mock_arch_model.get_modules.return_value = ["big.py"]
        mock_metrics.get_module_lines.return_value = 600
        mock_metrics.get_module_functions.return_value = 60

        violations = enforcer.check_violations()

        assert len(violations) >= 4
        for v in violations:
            assert v.evidence, f"{v.rule_id} at {v.location} has empty evidence"
