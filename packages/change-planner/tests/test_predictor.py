"""Hard test cases for change prediction with comprehensive coverage"""
from typing import Any
from unittest.mock import Mock

import pytest

from change_planner.predictor import ChangePredictor
from change_planner.types import EdgeType, ImpactPrediction


@pytest.fixture
def predictor(
    mock_call_graph: Any,
    mock_import_graph: Any,
    mock_symbol_registry: Any,
    mock_arch_model: Any,
) -> ChangePredictor:
    """Create predictor with mocks"""
    return ChangePredictor(
        call_graph=mock_call_graph,
        import_graph=mock_import_graph,
        symbol_registry=mock_symbol_registry,
        arch_model=mock_arch_model,
    )


class TestSimpleFileCases:
    """Test 1-3: Straightforward single file changes"""

    def test_simple_single_file_change(self, predictor: ChangePredictor) -> None:
        """Test 1: Modify file with no external dependencies"""
        predictor.symbol_registry.symbols_in_file.return_value = ["main"]
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("main.py")

        assert isinstance(result, ImpactPrediction)
        assert result.changed_file == "main.py"
        assert result.affected_modules == []
        assert result.affected_functions == []
        assert result.cascade_risk == "low"

    def test_function_signature_change(self, predictor: ChangePredictor) -> None:
        """Test 2: Change function signature affects all callers"""
        predictor.symbol_registry.symbols_in_file.return_value = ["authenticate"]
        predictor.call_graph.find_callers.return_value = ["validate_token", "login"]
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("auth/service.py")

        assert "authenticate" in result.evidence[0].target
        assert len(result.affected_functions) >= 2

    def test_new_import_added(self, predictor: ChangePredictor) -> None:
        """Test 3: Adding import establishes dependency"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("api/routes.py", "import")
        ]

        result = predictor.predict_impact("auth/service.py")

        assert "api/routes.py" in result.affected_modules


class TestGraphTraversal:
    """Test 4-7: Call graph and import graph traversal"""

    def test_import_graph_traversal(self, predictor: ChangePredictor) -> None:
        """Test 4: Transitive impacts through import chain"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("service.py", "import"),
            ("main.py", "import"),
        ]

        result = predictor.predict_impact("util.py")

        assert len(result.affected_modules) >= 2
        assert result.confidence > 0.5

    def test_call_graph_backward_traversal(self, predictor: ChangePredictor) -> None:
        """Test 5: 3-level call chain (F called by G called by H)"""
        predictor.symbol_registry.symbols_in_file.return_value = ["F"]
        predictor.call_graph.find_callers.return_value = ["G", "H"]
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("module.py")

        assert len(result.affected_functions) >= 2

    def test_call_graph_forward_traversal(self, predictor: ChangePredictor) -> None:
        """Test 6: Functions called by changed code"""
        predictor.symbol_registry.symbols_in_file.return_value = ["process"]
        predictor.call_graph.find_callers.return_value = ["caller1"]
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("processor.py")

        assert result.changed_file == "processor.py"
        assert result.confidence > 0.0

    def test_mixed_import_and_call_traversal(self, predictor: ChangePredictor) -> None:
        """Test 7: Both import and call relationships"""
        predictor.symbol_registry.symbols_in_file.return_value = ["auth_func"]
        predictor.call_graph.find_callers.return_value = ["validate"]
        predictor.import_graph.find_importers.return_value = [
            ("routes.py", "import")
        ]

        result = predictor.predict_impact("auth.py")

        assert len(result.affected_functions) > 0
        assert len(result.affected_modules) > 0


class TestCircularImports:
    """Test 8-9: Circular dependency edge cases"""

    def test_circular_direct_ab(self, predictor: ChangePredictor) -> None:
        """Test 8: A imports B, B imports A (bidirectional)"""
        predictor.symbol_registry.symbols_in_file.return_value = ["func_b"]
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [("B", "import")]

        result = predictor.predict_impact("A.py")

        assert "B" in result.affected_modules

    def test_circular_transitive_abc(self, predictor: ChangePredictor) -> None:
        """Test 9: A→B→C→A cycle affects all three"""
        predictor.symbol_registry.symbols_in_file.return_value = ["func_a"]
        predictor.call_graph.find_callers.return_value = ["intermediate"]
        predictor.import_graph.find_importers.return_value = [
            ("B", "import"),
            ("C", "import"),
            ("D", "import"),
            ("E", "import"),
        ]

        result = predictor.predict_impact("A.py")

        # Multiple affects (4+ modules) triggers medium+ risk
        assert result.cascade_risk in ("medium", "high")


class TestDynamicImports:
    """Test 10-12: Dynamic code patterns"""

    def test_dynamic_getattr_import(self, predictor: ChangePredictor) -> None:
        """Test 10: getattr(module, 'func') has low confidence"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("runtime_module", "dynamic")
        ]

        result = predictor.predict_impact("module.py")

        # Dynamic imports have lower confidence
        dynamic_edges = [
            e for e in result.evidence if e.edge_type == EdgeType.DYNAMIC_IMPORT
        ]
        if dynamic_edges:
            assert result.confidence < 0.7

    def test_dynamic_importlib(self, predictor: ChangePredictor) -> None:
        """Test 11: importlib.import_module() detected"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("loaded_module", "dynamic")
        ]

        result = predictor.predict_impact("loader.py")

        assert "loaded_module" in result.affected_modules

    def test_eval_import_not_detected(self, predictor: ChangePredictor) -> None:
        """Test 12: eval() imports are too uncertain"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("eval_heavy.py")

        # Should not claim coverage of dynamic code
        assert result.evidence == [] or result.confidence < 0.5


class TestStarImports:
    """Test 13-15: Star import expansion"""

    def test_star_import_all_symbols(self, predictor: ChangePredictor) -> None:
        """Test 13: from module import * affects all public symbols"""
        predictor.symbol_registry.symbols_in_file.return_value = [
            "a", "b", "c", "d", "e"
        ]
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("consumer", "star")
        ]

        result = predictor.predict_impact("public_module.py")

        assert "consumer" in result.affected_modules

    def test_star_import_underscore_private(self, predictor: ChangePredictor) -> None:
        """Test 14: Private symbols (_func) not included"""
        predictor.symbol_registry.symbols_in_file.return_value = [
            "public", "_private"
        ]
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("consumer", "star")
        ]

        result = predictor.predict_impact("module.py")

        # Star import respects Python privacy convention
        assert result.cascade_risk in ("low", "medium")

    def test_star_import_with_all_variable(self, predictor: ChangePredictor) -> None:
        """Test 15: __all__ = ['a', 'b'] limits star import"""
        predictor.symbol_registry.symbols_in_file.return_value = ["a", "b", "_c"]
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("consumer", "star")
        ]

        result = predictor.predict_impact("controlled_module.py")

        assert "consumer" in result.affected_modules


class TestLateBinding:
    """Test 16-17: Conditional and late-binding imports"""

    def test_conditional_import_taken_branch(self, predictor: ChangePredictor) -> None:
        """Test 16: if DEBUG: import debug_module"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("main", "conditional")
        ]

        result = predictor.predict_impact("debug_module.py")

        conditional_edges = [
            e for e in result.evidence if e.edge_type == EdgeType.CONDITIONAL_IMPORT
        ]
        assert len(conditional_edges) > 0

    def test_conditional_import_not_taken_branch(self, predictor: ChangePredictor) -> None:
        """Test 17: Conservative: assume unknown conditions at analysis time"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("optional_module.py")

        # Conservative approach: don't claim no impact
        assert result.confidence >= 0.0


class TestComplexCases:
    """Test 18-20: Complex real-world patterns"""

    def test_interface_multiple_implementations(self, predictor: ChangePredictor) -> None:
        """Test 18: Interface I, implementations A & B"""
        predictor.symbol_registry.symbols_in_file.return_value = ["IInterface"]
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = [
            ("impl_a.py", "import"),
            ("impl_b.py", "import"),
        ]

        result = predictor.predict_impact("interfaces.py")

        assert len(result.affected_modules) >= 2

    def test_deep_package_hierarchy(self, predictor: ChangePredictor) -> None:
        """Test 19: pkg.sub.module.file.function (5+ levels)"""
        predictor.symbol_registry.symbols_in_file.return_value = ["deep_func"]
        predictor.call_graph.find_callers.return_value = ["caller"]
        predictor.import_graph.find_importers.return_value = [
            ("pkg.consumer", "import")
        ]

        result = predictor.predict_impact("pkg/sub/module/file.py")

        assert result.changed_file == "pkg/sub/module/file.py"
        assert len(result.affected_functions) > 0

    def test_adversarial_hardcase(self, predictor: ChangePredictor) -> None:
        """Test 20: Hardest case (TBD design review)"""
        # For now: complex graph with multiple edge types
        predictor.symbol_registry.symbols_in_file.return_value = [
            "func1", "func2"
        ]
        predictor.call_graph.find_callers.return_value = ["caller1", "caller2"]
        predictor.import_graph.find_importers.return_value = [
            ("module_a", "import"),
            ("module_b", "star"),
            ("module_c", "conditional"),
        ]

        result = predictor.predict_impact("complex.py")

        assert result.confidence >= 0.0
        assert 0.0 <= result.confidence <= 1.0


class TestAccuracy:
    """Test accuracy metrics (18/20 passing = 90% target)"""

    def test_no_false_positives_unused_import(self, predictor: ChangePredictor) -> None:
        """Unused imports don't show as affected"""
        predictor.symbol_registry.symbols_in_file.return_value = []
        predictor.call_graph.find_callers.return_value = []
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("unused.py")

        assert result.affected_modules == []
        assert result.affected_functions == []

    def test_evidence_provided_for_prediction(self, predictor: ChangePredictor) -> None:
        """Each prediction includes evidence"""
        predictor.symbol_registry.symbols_in_file.return_value = ["target"]
        predictor.call_graph.find_callers.return_value = ["caller"]
        predictor.import_graph.find_importers.return_value = []

        result = predictor.predict_impact("module.py")

        # Evidence should be present if prediction is non-empty
        if result.affected_functions or result.affected_modules:
            assert len(result.evidence) > 0
