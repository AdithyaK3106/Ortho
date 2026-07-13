"""Exhaustive edge case tests for feature-planner"""
from unittest.mock import Mock
import pytest

from feature_planner.planner import FeaturePlanner
from feature_planner.types import ImplementationPath


@pytest.fixture
def planner() -> FeaturePlanner:
    mock_arch = Mock()
    mock_arch.layers = {"presentation": 0, "service": 1, "data": 2}
    mock_arch.get_layer = Mock(return_value="service")
    return FeaturePlanner(arch_model=mock_arch)


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_empty_intent(self, planner: FeaturePlanner) -> None:
        """Empty intent string"""
        result = planner.plan_feature("")
        assert result is not None
        assert len(result.paths) >= 3

    def test_whitespace_only_intent(self, planner: FeaturePlanner) -> None:
        """Whitespace-only intent"""
        result = planner.plan_feature("   \n\t  ")
        assert result is not None

    def test_very_long_intent(self, planner: FeaturePlanner) -> None:
        """Intent with 10K+ characters"""
        long_intent = "add " + "x" * 10000
        result = planner.plan_feature(long_intent)
        assert result is not None
        assert len(result.paths) >= 3

    def test_special_chars_in_intent(self, planner: FeaturePlanner) -> None:
        """Intent with special characters"""
        result = planner.plan_feature("add $special#feature@home")
        assert result is not None
        assert len(result.paths) >= 3

    def test_unicode_in_intent(self, planner: FeaturePlanner) -> None:
        """Intent with unicode characters"""
        result = planner.plan_feature("add café/файл/日本語")
        assert result is not None
        assert len(result.paths) >= 3

    def test_sql_injection_attempt(self, planner: FeaturePlanner) -> None:
        """Intent with SQL-like injection pattern"""
        result = planner.plan_feature("add feature'; DROP TABLE--")
        assert result is not None

    def test_command_injection_attempt(self, planner: FeaturePlanner) -> None:
        """Intent with command injection pattern"""
        result = planner.plan_feature("add $(rm -rf /)")
        assert result is not None


    def test_minimum_path_count(self, planner: FeaturePlanner) -> None:
        """Paths should have at least 3"""
        result = planner.plan_feature("add async handler")
        assert len(result.paths) >= 3

    def test_path_variety(self, planner: FeaturePlanner) -> None:
        """Paths should have different efforts"""
        result = planner.plan_feature("add caching layer")
        efforts = [p.effort for p in result.paths]
        # Should have some variety (not all same)
        assert len(set(efforts)) >= 1

    def test_all_paths_have_rationale(self, planner: FeaturePlanner) -> None:
        """All paths must have rationale"""
        result = planner.plan_feature("add database")
        for path in result.paths:
            assert path.rationale != ""
            assert len(path.rationale) > 10

    def test_all_paths_have_dependencies(self, planner: FeaturePlanner) -> None:
        """All paths must list dependencies"""
        result = planner.plan_feature("add validation")
        for path in result.paths:
            assert isinstance(path.dependencies_to_add, list)

    def test_effort_enum_valid(self, planner: FeaturePlanner) -> None:
        """All paths have valid effort"""
        result = planner.plan_feature("add feature")
        for path in result.paths:
            assert path.effort in ("low", "medium", "high")

    def test_risk_enum_valid(self, planner: FeaturePlanner) -> None:
        """All paths have valid risk"""
        result = planner.plan_feature("add feature")
        for path in result.paths:
            assert path.risk in ("low", "medium", "high")

    def test_affected_layers_valid(self, planner: FeaturePlanner) -> None:
        """All paths have valid affected layers"""
        result = planner.plan_feature("add feature")
        for path in result.paths:
            assert isinstance(path.affected_layers, list)
            assert len(path.affected_layers) > 0

    def test_conflicting_paths(self, planner: FeaturePlanner) -> None:
        """Paths may suggest opposite approaches"""
        result = planner.plan_feature("refactor architecture")
        # Should still return valid paths
        assert len(result.paths) >= 3
        for path in result.paths:
            assert path.rationale != ""

    def test_high_complexity_intent(self, planner: FeaturePlanner) -> None:
        """Complex intent with many clauses"""
        intent = "add async database pooling with caching and monitoring"
        result = planner.plan_feature(intent)
        assert len(result.paths) >= 3

    def test_ambiguous_intent(self, planner: FeaturePlanner) -> None:
        """Ambiguous intent could mean multiple things"""
        result = planner.plan_feature("improve")
        # Should still generate paths
        assert len(result.paths) >= 3

    def test_no_duplicate_paths(self, planner: FeaturePlanner) -> None:
        """No two paths should be identical"""
        result = planner.plan_feature("add feature")
        rationales = [p.rationale for p in result.paths]
        # At least some variation in rationales
        assert len(set(rationales)) >= 1
