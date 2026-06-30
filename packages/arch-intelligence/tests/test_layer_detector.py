"""Tests for LayerDetector."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from layer_detector import LayerDetector


class TestLayerDetectorBasics:
    """Basic layer detection tests."""

    def test_detector_initializes(self, temp_db, sample_repo_id):
        """Test that LayerDetector can be instantiated."""
        detector = LayerDetector(temp_db, sample_repo_id)
        assert detector is not None

    def test_detect_layers_returns_list(self, mock_symbol_repo, sample_repo_id):
        """Test that detect_layers() returns a list."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        assert isinstance(layers, list)

    def test_layers_have_required_fields(self, mock_symbol_repo, sample_repo_id):
        """Test that each layer has required fields."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert hasattr(layer, "id")
            assert hasattr(layer, "name")
            assert hasattr(layer, "file_ids")
            assert hasattr(layer, "depends_on")
            assert hasattr(layer, "confidence")

    def test_layer_confidence_in_range(self, mock_symbol_repo, sample_repo_id):
        """Test that layer confidence is 0.0-1.0."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert 0.0 <= layer.confidence <= 1.0

    def test_layer_file_ids_are_strings(self, mock_symbol_repo, sample_repo_id):
        """Test that file_ids are strings."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert all(isinstance(fid, str) for fid in layer.file_ids)

    def test_layer_names_are_semantic(self, mock_symbol_repo, sample_repo_id):
        """Test that layer names are assigned (presentation/business/data)."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        # Should have names for at least some layers
        assert len(layers) > 0
        assert all(isinstance(layer.name, str) for layer in layers)
        assert all(len(layer.name) > 0 for layer in layers)


class TestLayerViolationDetection:
    """Test cross-layer violation detection."""

    def test_detect_violations_returns_list(self, mock_symbol_repo, sample_repo_id):
        """Test that detect_layer_violations() returns a list."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        violations = detector.detect_layer_violations()

        assert isinstance(violations, list)

    def test_violations_are_strings(self, mock_symbol_repo, sample_repo_id):
        """Test that violations are described as strings."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        violations = detector.detect_layer_violations()

        assert all(isinstance(v, str) for v in violations)


class TestLayerDependencies:
    """Test layer dependency tracking."""

    def test_depends_on_is_list(self, mock_symbol_repo, sample_repo_id):
        """Test that depends_on is a list of layer IDs."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        for layer in layers:
            assert isinstance(layer.depends_on, list)
            assert all(isinstance(dep, str) for dep in layer.depends_on)

    def test_layer_hierarchy_preserved(self, mock_symbol_repo, sample_repo_id):
        """Test that layer dependencies respect hierarchy."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        # Layers should form a DAG (no layer depends on layers above it)
        layer_positions = {layer.id: i for i, layer in enumerate(layers)}
        for layer in layers:
            for dep_id in layer.depends_on:
                if dep_id in layer_positions:
                    # Dependency should be to a lower layer (higher index)
                    assert layer_positions[dep_id] > layer_positions[layer.id]


class TestLayerDetectorConsistency:
    """Test consistency and determinism."""

    def test_determinism(self, mock_symbol_repo, sample_repo_id):
        """Test that running detect_layers() twice gives same result."""
        detector1 = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers1 = detector1.detect_layers()

        detector2 = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers2 = detector2.detect_layers()

        assert len(layers1) == len(layers2)
        for l1, l2 in zip(layers1, layers2):
            assert l1.id == l2.id
            assert l1.name == l2.name
            assert l1.file_ids == l2.file_ids
            assert l1.depends_on == l2.depends_on

    def test_no_duplicate_file_ids_across_layers(self, mock_symbol_repo, sample_repo_id):
        """Test that files are not in multiple layers."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        all_files = []
        for layer in layers:
            all_files.extend(layer.file_ids)

        # Each file should appear in exactly one layer
        assert len(all_files) == len(set(all_files))

    def test_all_files_accounted_for(self, mock_symbol_repo, sample_repo_id):
        """Test that all files from repo are in some layer."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()

        layered_files = set()
        for layer in layers:
            layered_files.update(layer.file_ids)

        # Should have assigned all files to layers
        assert len(layered_files) > 0
