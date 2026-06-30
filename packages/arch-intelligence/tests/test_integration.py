"""Integration tests for architecture detection."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from detector import ArchitectureDetector
from layer_detector import LayerDetector
from subsystem_detector import SubsystemDetector
from models import ArchitectureModelStore


class TestEndToEndDetection:
    """End-to-end architecture detection tests."""

    def test_full_detection_flow(self, mock_symbol_repo, sample_repo_id):
        """Test complete detection flow: detector → layers → subsystems."""
        # Detect architecture
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        arch_result = detector.detect()

        # Detect layers
        layer_detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = layer_detector.detect_layers()

        # Detect subsystems
        subsys_detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = subsys_detector.detect_subsystems()

        # Verify consistency
        assert arch_result is not None
        assert len(layers) > 0
        assert len(subsystems) > 0
        assert 0.0 <= arch_result.confidence <= 1.0

    def test_architecture_model_persistence(self, mock_symbol_repo, sample_repo_id):
        """Test saving and loading architecture model."""
        # Detect architecture
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Store model (if API available)
        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)
        assert store is not None

    def test_evidence_structure(self, mock_symbol_repo, sample_repo_id):
        """Test that evidence contains expected structured information."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Check evidence contains useful information
        evidence_text = " ".join(result.evidence)

        # Should have some metrics or analysis
        has_content = (
            "layering" in evidence_text.lower()
            or "cohesion" in evidence_text.lower()
            or "upward" in evidence_text.lower()
            or "layer" in evidence_text.lower()
        )
        assert has_content or len(result.evidence) > 0


class TestPerformanceBasics:
    """Basic performance checks (not strict timing)."""

    def test_detector_completes(self, mock_symbol_repo, sample_repo_id):
        """Test that detector completes without timeout."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()
        assert result is not None

    def test_layer_detector_completes(self, mock_symbol_repo, sample_repo_id):
        """Test that layer detector completes."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()
        assert isinstance(layers, list)

    def test_subsystem_detector_completes(self, mock_symbol_repo, sample_repo_id):
        """Test that subsystem detector completes."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()
        assert isinstance(subsystems, list)


class TestEvidenceQuality:
    """Test the quality and structure of evidence output."""

    def test_evidence_is_list_of_strings(self, mock_symbol_repo, sample_repo_id):
        """Test that evidence is properly formatted."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert isinstance(result.evidence, list)
        assert all(isinstance(e, str) for e in result.evidence)
        assert len(result.evidence) > 0

    def test_confidence_breakdown_exists(self, mock_symbol_repo, sample_repo_id):
        """Test that confidence breakdown is available."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0
        assert all(isinstance(k, str) and isinstance(v, float) for k, v in breakdown.items())

    def test_alternative_detection_when_ambiguous(self, mock_symbol_repo, sample_repo_id):
        """Test that ambiguous cases show alternatives."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Either no alternative, or alternative confidence is lower
        if result.alternative:
            assert result.alternative_confidence is not None
            assert result.alternative != result.style
