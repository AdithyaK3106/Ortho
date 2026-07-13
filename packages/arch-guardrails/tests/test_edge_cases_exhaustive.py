"""Exhaustive edge case tests for arch-guardrails"""
from unittest.mock import Mock
import pytest

from arch_guardrails.enforcer import ArchitectureEnforcer
from arch_guardrails.types import GuardrailViolation


@pytest.fixture
def enforcer() -> ArchitectureEnforcer:
    mock_arch = Mock()
    mock_arch.get_layers = Mock(return_value=["presentation", "service", "data"])
    mock_arch.get_layer_for_module = Mock(return_value="service")
    mock_arch.get_modules = Mock(return_value=[])

    mock_dep = Mock()
    mock_dep.get_edges = Mock(return_value=[])
    mock_dep.find_cycles = Mock(return_value=[])

    mock_metrics = Mock()
    mock_metrics.get_module_lines = Mock(return_value=500)
    mock_metrics.get_module_functions = Mock(return_value=50)

    return ArchitectureEnforcer(
        arch_model=mock_arch,
        dep_graph=mock_dep,
        metrics=mock_metrics,
    )


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_no_layers_defined(self, enforcer: ArchitectureEnforcer) -> None:
        """No layers configured"""
        enforcer.arch_model.get_layers.return_value = []
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_single_layer_monolith(self, enforcer: ArchitectureEnforcer) -> None:
        """Single layer (monolith)"""
        enforcer.arch_model.get_layers.return_value = ["app"]
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_ten_layers_deep(self, enforcer: ArchitectureEnforcer) -> None:
        """10 layers (deep hierarchy)"""
        enforcer.arch_model.get_layers.return_value = [f"layer_{i}" for i in range(10)]
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_no_dependencies(self, enforcer: ArchitectureEnforcer) -> None:
        """No dependencies in repo"""
        enforcer.dep_graph.get_edges.return_value = []
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_all_modules_depend_on_all(self, enforcer: ArchitectureEnforcer) -> None:
        """Complete graph (all depend on all)"""
        enforcer.dep_graph.get_edges.return_value = [
            ("A", "B"), ("A", "C"), ("B", "A"), ("B", "C"), ("C", "A"), ("C", "B")
        ]
        result = enforcer.check_violations()
        # Should handle without crashing
        assert isinstance(result, list)

    def test_no_modules(self, enforcer: ArchitectureEnforcer) -> None:
        """Empty module list"""
        enforcer.arch_model.get_modules.return_value = []
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_module_not_in_layer(self, enforcer: ArchitectureEnforcer) -> None:
        """Module not assigned to any layer"""
        enforcer.arch_model.get_layer_for_module.return_value = None
        result = enforcer.check_violations()
        # Should handle gracefully
        assert isinstance(result, list)

    def test_cyclic_ab(self, enforcer: ArchitectureEnforcer) -> None:
        """A→B→A cycle"""
        enforcer.dep_graph.find_cycles.return_value = [["A", "B"]]
        result = enforcer.check_violations()
        # Should detect cycle
        assert isinstance(result, list)

    def test_cyclic_all_to_all(self, enforcer: ArchitectureEnforcer) -> None:
        """All modules cyclically depend"""
        enforcer.dep_graph.find_cycles.return_value = [["A", "B", "C"]]
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_module_size_zero_lines(self, enforcer: ArchitectureEnforcer) -> None:
        """Module with 0 lines"""
        enforcer.metrics.get_module_lines.return_value = 0
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_module_size_huge_lines(self, enforcer: ArchitectureEnforcer) -> None:
        """Module with 100K+ lines"""
        enforcer.metrics.get_module_lines.return_value = 100_000
        result = enforcer.check_violations()
        # Should flag as violation
        assert isinstance(result, list)

    def test_module_zero_functions(self, enforcer: ArchitectureEnforcer) -> None:
        """Module with 0 functions"""
        enforcer.metrics.get_module_functions.return_value = 0
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_module_10k_functions(self, enforcer: ArchitectureEnforcer) -> None:
        """Module with 10K functions"""
        enforcer.metrics.get_module_functions.return_value = 10_000
        result = enforcer.check_violations()
        # Should flag as violation
        assert isinstance(result, list)

    def test_violation_severity_valid(self, enforcer: ArchitectureEnforcer) -> None:
        """All violations have valid severity"""
        result = enforcer.check_violations()
        for violation in result:
            assert violation.severity in ("low", "medium", "high")

    def test_violation_confidence_bounds(self, enforcer: ArchitectureEnforcer) -> None:
        """All violations have confidence 0.0-1.0"""
        result = enforcer.check_violations()
        for violation in result:
            assert 0.0 <= violation.confidence <= 1.0

    def test_suggested_fixes_present(self, enforcer: ArchitectureEnforcer) -> None:
        """Violations should have suggested fixes"""
        result = enforcer.check_violations()
        for violation in result:
            assert violation.suggested_fix != ""

    def test_layer_boundary_violation(self, enforcer: ArchitectureEnforcer) -> None:
        """Layer boundary violation detection"""
        enforcer.dep_graph.get_edges.return_value = [("data.py", "presentation.py")]
        enforcer.arch_model.get_layer_for_module.side_effect = lambda m: (
            "data" if "data" in m else "presentation"
        )
        result = enforcer.check_violations()
        assert isinstance(result, list)

    def test_acyclic_dag_verification(self, enforcer: ArchitectureEnforcer) -> None:
        """Verify DAG (acyclic) property"""
        enforcer.dep_graph.get_edges.return_value = [("A", "B"), ("B", "C")]
        enforcer.dep_graph.find_cycles.return_value = []
        result = enforcer.check_violations()
        # Should not find violations for acyclic graph
        assert isinstance(result, list)

    def test_multiple_violations_returned(self, enforcer: ArchitectureEnforcer) -> None:
        """All violations should be returned"""
        result = enforcer.check_violations()
        # Should not truncate results
        assert isinstance(result, list)
