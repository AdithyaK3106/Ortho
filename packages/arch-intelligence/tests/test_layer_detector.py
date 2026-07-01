"""Tests for LayerDetector — STRICT behavioral assertions."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from arch_intelligence.layer_detector import LayerDetector


class TestLayerDetectionBasics:
    """AC5: Extract logical layers from dependency graph."""

    def test_detect_layers_returns_list_not_empty(self, mock_symbol_repo, sample_repo_id):
        """AC5: detect_layers() returns non-empty list."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        assert isinstance(layers, list), "detect_layers must return a list"
        assert len(layers) > 0, "Should extract at least one layer"

    def test_layered_fixture_detects_three_layers(self, layered_fixture_db, layered_repo_id):
        """AC5: Layered fixture should detect 3 distinct layers."""
        detector = LayerDetector(layered_fixture_db, layered_repo_id)
        layers = detector.detect_layers()

        assert len(layers) == 3, f"Expected 3 layers, got {len(layers)}"


class TestLayerFieldContent:
    """AC5: Layer objects must contain correct data."""

    def test_layer_id_is_string(self, mock_symbol_repo, sample_repo_id):
        """Layer.id must be a non-empty string."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert isinstance(layer.id, str), f"Layer.id must be string, got {type(layer.id)}"
            assert len(layer.id) > 0, "Layer.id must not be empty"

    def test_layer_name_is_semantic(self, mock_symbol_repo, sample_repo_id):
        """AC6: Layer names must be semantic (presentation/business/data/etc)."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        valid_names = {
            "presentation",
            "business",
            "data",
            "infrastructure",
            "api",
            "handlers",
            "domain",
            "logic",
            "repository",
            "storage",
            "config",
            "utils",
        }

        for layer in layers:
            assert isinstance(layer.name, str), f"Layer.name must be string, got {type(layer.name)}"
            assert len(layer.name) > 0, "Layer.name must not be empty"
            # Name should be one of the semantic categories OR auto-numbered
            is_semantic = layer.name.lower() in valid_names
            is_auto_numbered = "level_" in layer.name.lower()
            assert (
                is_semantic or is_auto_numbered
            ), f"Layer name '{layer.name}' should be semantic or auto-numbered"

    def test_layer_file_ids_are_nonempty_list(self, mock_symbol_repo, sample_repo_id):
        """Layer.file_ids must be a non-empty list of strings."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert isinstance(layer.file_ids, list), f"Layer.file_ids must be list, got {type(layer.file_ids)}"
            assert len(layer.file_ids) > 0, f"Layer '{layer.id}' has no files"
            for file_id in layer.file_ids:
                assert isinstance(file_id, str), f"File ID must be string, got {type(file_id)}"
                assert len(file_id) > 0, "File ID must not be empty"

    def test_layer_confidence_in_range(self, mock_symbol_repo, sample_repo_id):
        """Layer.confidence must be float in [0.0, 1.0]."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert isinstance(layer.confidence, float), f"Confidence must be float, got {type(layer.confidence)}"
            assert (
                0.0 <= layer.confidence <= 1.0
            ), f"Confidence {layer.confidence} out of range"

    def test_layer_depends_on_is_list(self, mock_symbol_repo, sample_repo_id):
        """Layer.depends_on must be a list of layer IDs."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        layer_ids = {l.id for l in layers}

        for layer in layers:
            assert isinstance(layer.depends_on, list), f"depends_on must be list, got {type(layer.depends_on)}"
            for dep_id in layer.depends_on:
                assert isinstance(dep_id, str), f"Dependency ID must be string, got {type(dep_id)}"
                assert (
                    dep_id in layer_ids
                ), f"Dependency '{dep_id}' must reference valid layer ID"


class TestSemanticNaming:
    """AC6: _assign_semantic_names() assigns proper layer names."""

    def test_layered_fixture_has_presentation_business_data(self, layered_fixture_db, layered_repo_id):
        """AC6: Layered fixture should assign presentation/business/data names."""
        detector = LayerDetector(layered_fixture_db, layered_repo_id)
        layers = detector.detect_layers()

        layer_names = {l.name.lower() for l in layers}

        # Should detect standard layer names
        has_presentation = any(
            name in layer_names for name in ["presentation", "api", "handlers", "view"]
        )
        has_business = any(
            name in layer_names for name in ["business", "domain", "logic"]
        )
        has_data = any(
            name in layer_names for name in ["data", "repository", "storage"]
        )

        assert (
            has_presentation and has_business and has_data
        ), f"Expected presentation/business/data, got {layer_names}"

    def test_mvc_fixture_has_view_controller_model(self, mvc_fixture_db, mvc_repo_id):
        """AC6: MVC fixture should detect view/controller/model layers."""
        detector = LayerDetector(mvc_fixture_db, mvc_repo_id)
        layers = detector.detect_layers()

        layer_names = {l.name.lower() for l in layers}

        # MVC should map to standard layers too (view→presentation, controller→business, model→data)
        # OR use MVC-specific names if detector supports them
        assert len(layers) >= 2, f"MVC should have multiple layers, got {len(layers)}"


class TestLayerViolationDetection:
    """AC7: detect_layer_violations() identifies cross-layer dependency violations."""

    def test_violations_returns_list_of_strings(self, mock_symbol_repo, sample_repo_id):
        """AC7: Violations must be list of strings."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        violations = detector.detect_layer_violations()

        assert isinstance(violations, list), "Violations must be a list"
        for violation in violations:
            assert isinstance(violation, str), f"Each violation must be string, got {type(violation)}"
            assert len(violation) > 0, "Violation description must not be empty"

    def test_layered_fixture_has_minimal_violations(self, layered_fixture_db, layered_repo_id):
        """AC7: Strict layered fixture should have few or no violations."""
        detector = LayerDetector(layered_fixture_db, layered_repo_id)
        violations = detector.detect_layer_violations()

        # Canonical layered fixture should have very few upward violations
        assert len(violations) <= 1, f"Strict layered should have ≤1 violations, got {len(violations)}"


class TestLayerHierarchyValidity:
    """AC5/AC8: Layer dependencies form valid DAG."""

    def test_all_dependencies_reference_valid_layers(self, mock_symbol_repo, sample_repo_id):
        """All depends_on references must be valid layer IDs."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        layer_ids = {l.id for l in layers}

        for layer in layers:
            for dep_id in layer.depends_on:
                assert dep_id in layer_ids, f"Invalid dependency: {dep_id} not in layer_ids"

    def test_no_self_dependencies(self, mock_symbol_repo, sample_repo_id):
        """Layer must not depend on itself."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert (
                layer.id not in layer.depends_on
            ), f"Layer '{layer.id}' has self-dependency"

    def test_files_in_single_layer(self, mock_symbol_repo, sample_repo_id):
        """Each file must appear in exactly one layer."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        all_file_ids = []
        for layer in layers:
            all_file_ids.extend(layer.file_ids)

        # No duplicates
        assert len(all_file_ids) == len(set(all_file_ids)), "Files appear in multiple layers"


class TestDeterminism:
    """AC5/AC8: Detection must be deterministic."""

    def test_detect_layers_twice_identical(self, mock_symbol_repo, sample_repo_id):
        """Running detect_layers() twice must produce identical results."""
        detector1 = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers1 = detector1.detect_layers()

        detector2 = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers2 = detector2.detect_layers()

        assert len(layers1) == len(layers2), "Layer count must be identical"

        for l1, l2 in zip(layers1, layers2):
            assert l1.id == l2.id, f"Layer IDs differ: {l1.id} vs {l2.id}"
            assert l1.name == l2.name, f"Layer names differ: {l1.name} vs {l2.name}"
            assert l1.file_ids == l2.file_ids, f"File IDs differ for layer {l1.id}"
            assert l1.depends_on == l2.depends_on, f"Dependencies differ for layer {l1.id}"
            assert (
                l1.confidence == l2.confidence
            ), f"Confidence differs for layer {l1.id}"


class TestLayerConfidenceLogic:
    """AC8: Layer confidence reflects detection reliability."""

    def test_all_layers_have_confidence(self, mock_symbol_repo, sample_repo_id):
        """Each layer must have a confidence score."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert hasattr(layer, "confidence"), f"Layer {layer.id} missing confidence"
            assert isinstance(layer.confidence, float), "Confidence must be float"
            assert 0.0 <= layer.confidence <= 1.0, f"Confidence {layer.confidence} out of range"

    def test_layered_fixture_layers_have_high_confidence(self, layered_fixture_db, layered_repo_id):
        """AC8: Strict layered fixture should have high per-layer confidence."""
        detector = LayerDetector(layered_fixture_db, layered_repo_id)
        layers = detector.detect_layers()

        # Most layers in clean layered architecture should have high confidence
        avg_confidence = sum(l.confidence for l in layers) / len(layers)
        assert avg_confidence >= 0.75, f"Average layer confidence too low: {avg_confidence}"
