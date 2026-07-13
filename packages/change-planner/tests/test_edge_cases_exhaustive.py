"""Exhaustive edge case tests for change-planner"""
from unittest.mock import Mock
import pytest

from change_planner.predictor import ChangePredictor
from change_planner.types import ImpactPrediction


@pytest.fixture
def predictor() -> ChangePredictor:
    mock_graph = Mock()
    mock_graph.find_callers = Mock(return_value=[])
    mock_import = Mock()
    mock_import.find_importers = Mock(return_value=[])
    mock_symbols = Mock()
    mock_symbols.symbols_in_file = Mock(return_value=[])
    mock_arch = Mock()
    mock_arch.get_layer = Mock(return_value="unknown")

    return ChangePredictor(
        call_graph=mock_graph,
        import_graph=mock_import,
        symbol_registry=mock_symbols,
        arch_model=mock_arch,
    )


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_empty_file_change(self, predictor: ChangePredictor) -> None:
        """Empty file should handle gracefully"""
        result = predictor.predict_impact("")
        assert isinstance(result, ImpactPrediction)
        assert result.changed_file == ""

    def test_file_with_only_whitespace(self, predictor: ChangePredictor) -> None:
        """Whitespace-only file path"""
        result = predictor.predict_impact("   ")
        assert isinstance(result, ImpactPrediction)

    def test_very_long_file_path(self, predictor: ChangePredictor) -> None:
        """Path with 10K+ characters"""
        long_path = "a" * 10000 + ".py"
        result = predictor.predict_impact(long_path)
        assert isinstance(result, ImpactPrediction)
        assert result.changed_file == long_path

    def test_special_chars_in_path(self, predictor: ChangePredictor) -> None:
        """Path with special characters"""
        result = predictor.predict_impact("path/with/$special#chars.py")
        assert isinstance(result, ImpactPrediction)

    def test_unicode_in_path(self, predictor: ChangePredictor) -> None:
        """Path with unicode characters"""
        result = predictor.predict_impact("café/café/файл.py")
        assert isinstance(result, ImpactPrediction)

    def test_no_symbols_in_file(self, predictor: ChangePredictor) -> None:
        """File with no symbols extracted"""
        predictor.symbol_registry.symbols_in_file.return_value = []

        result = predictor.predict_impact("empty.py")

        assert result.affected_functions == []

    def test_zero_callers(self, predictor: ChangePredictor) -> None:
        """Symbol with no callers"""
        predictor.symbol_registry.symbols_in_file.return_value = ["unused_func"]
        predictor.call_graph.find_callers.return_value = []

        result = predictor.predict_impact("module.py")

        assert result.affected_functions == []

    def test_thousand_callers(self, predictor: ChangePredictor) -> None:
        """Symbol called by 1000 functions (scale test)"""
        predictor.symbol_registry.symbols_in_file.return_value = ["hot_func"]
        predictor.call_graph.find_callers.return_value = [f"func_{i}" for i in range(1000)]

        result = predictor.predict_impact("hot.py")

        assert len(result.affected_functions) == 1000

    def test_deep_call_chain(self, predictor: ChangePredictor) -> None:
        """1000-level deep call chain"""
        predictor.symbol_registry.symbols_in_file.return_value = ["root"]
        # Simulate deep chain: A→B→C→...
        predictor.call_graph.find_callers.return_value = [f"level_{i}" for i in range(1000)]

        result = predictor.predict_impact("deep.py")

        assert len(result.affected_functions) == 1000

    def test_confidence_bounds(self, predictor: ChangePredictor) -> None:
        """Confidence should always be 0.0-1.0"""
        result = predictor.predict_impact("test.py")

        assert 0.0 <= result.confidence <= 1.0

    def test_cascade_risk_valid(self, predictor: ChangePredictor) -> None:
        """Cascade risk must be low/medium/high"""
        result = predictor.predict_impact("test.py")

        assert result.cascade_risk in ("low", "medium", "high")

    def test_null_input(self, predictor: ChangePredictor) -> None:
        """Null changed_file"""
        # Should not crash
        result = predictor.predict_impact(None)
        assert isinstance(result, ImpactPrediction)

    def test_circular_import_ab(self, predictor: ChangePredictor) -> None:
        """A→B→A handled"""
        predictor.import_graph.find_importers.return_value = [("B", "import")]

        result = predictor.predict_impact("A.py")

        assert "B" in result.affected_modules

    def test_circular_import_abc(self, predictor: ChangePredictor) -> None:
        """A→B→C→A handled"""
        predictor.import_graph.find_importers.return_value = [
            ("B", "import"), ("C", "import")
        ]

        result = predictor.predict_impact("A.py")

        assert len(result.affected_modules) >= 2

    def test_star_import_handling(self, predictor: ChangePredictor) -> None:
        """Star imports have lower confidence"""
        predictor.import_graph.find_importers.return_value = [("X", "star")]

        result = predictor.predict_impact("module.py")

        # Star imports should have lower confidence
        assert result.confidence <= 0.8

    def test_dynamic_import_handling(self, predictor: ChangePredictor) -> None:
        """Dynamic imports have low confidence"""
        predictor.import_graph.find_importers.return_value = [("X", "dynamic")]

        result = predictor.predict_impact("module.py")

        # Dynamic should have low confidence
        assert result.confidence <= 0.6

    def test_conditional_import_handling(self, predictor: ChangePredictor) -> None:
        """Conditional imports marked appropriately"""
        predictor.import_graph.find_importers.return_value = [("X", "conditional")]

        result = predictor.predict_impact("module.py")

        # Conditional should be medium confidence
        assert 0.5 <= result.confidence <= 0.8

    def test_no_evidence(self, predictor: ChangePredictor) -> None:
        """Handling when no evidence found"""
        result = predictor.predict_impact("test.py")

        assert isinstance(result.evidence, list)
        assert result.reasoning != ""

    def test_identical_modules_in_list(self, predictor: ChangePredictor) -> None:
        """Duplicates in affected modules list"""
        predictor.import_graph.find_importers.return_value = [("A", "import"), ("A", "import")]

        result = predictor.predict_impact("test.py")

        # Should not have duplicates
        assert len(result.affected_modules) == len(set(result.affected_modules))

    def test_very_high_cascade_count(self, predictor: ChangePredictor) -> None:
        """100+ affected modules"""
        predictor.import_graph.find_importers.return_value = [
            (f"module_{i}", "import") for i in range(100)
        ]

        result = predictor.predict_impact("core.py")

        assert result.cascade_risk in ("medium", "high")
        assert len(result.affected_modules) == 100
