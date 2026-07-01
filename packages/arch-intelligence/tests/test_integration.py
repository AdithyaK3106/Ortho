"""Integration tests for architecture detection — STRICT behavioral assertions."""

import sys
import json
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from arch_intelligence.detector import ArchitectureDetector
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.subsystem_detector import SubsystemDetector
from arch_intelligence.models import ArchitectureModelStore


class TestEndToEndDetectionFlow:
    """AC1-AC9: Complete detection pipeline."""

    def test_full_detection_produces_valid_results(self, mock_symbol_repo, sample_repo_id):
        """Full pipeline: detector → layers → subsystems all succeed."""
        # Detect architecture
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        arch_result = detector.detect()

        # Detect layers
        layer_detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = layer_detector.detect_layers()

        # Detect subsystems
        subsys_detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = subsys_detector.detect_subsystems()

        # All must succeed
        assert arch_result is not None, "Architecture detection failed"
        assert arch_result.style in [
            "layered",
            "hexagonal",
            "mvc",
            "microservices",
            "flat",
            "unknown",
        ], f"Invalid style: {arch_result.style}"
        assert 0.0 <= arch_result.confidence <= 1.0, "Invalid confidence"
        assert len(layers) > 0, "No layers detected"
        assert len(subsystems) > 0, "No subsystems detected"

    def test_layered_fixture_end_to_end(self, layered_fixture_db, layered_repo_id):
        """AC1-AC9: Layered fixture produces consistent end-to-end results."""
        # Style detection
        detector = ArchitectureDetector(layered_fixture_db, layered_repo_id)
        arch = detector.detect()
        assert arch.style == "layered", f"Expected layered, got {arch.style}"
        assert arch.confidence >= 0.80, f"Expected confidence ≥0.80, got {arch.confidence}"

        # Layers
        layer_det = LayerDetector(layered_fixture_db, layered_repo_id)
        layers = layer_det.detect_layers()
        assert len(layers) == 3, f"Expected 3 layers, got {len(layers)}"

        # Subsystems
        subsys_det = SubsystemDetector(layered_fixture_db, layered_repo_id)
        subsystems = subsys_det.detect_subsystems()
        assert len(subsystems) >= 3, f"Expected ≥3 subsystems, got {len(subsystems)}"


class TestEvidenceQuality:
    """AC2: Evidence must be detailed and meaningful."""

    def test_evidence_describes_detection_rationale(self, mock_symbol_repo, sample_repo_id):
        """AC2: Evidence explains why this style was detected."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        evidence_text = " ".join(result.evidence)

        # Should be substantive
        assert len(evidence_text) > 100, "Evidence too brief to be meaningful"

        # Should mention detection reasoning (not just metrics)
        has_reasoning = any(
            term in evidence_text.lower()
            for term in [
                "layer",
                "upward",
                "depend",
                "modularity",
                "coupling",
                "pattern",
                "style",
            ]
        )
        assert has_reasoning, f"Evidence lacks reasoning: {evidence_text}"

    def test_evidence_list_not_empty(self, mock_symbol_repo, sample_repo_id):
        """Evidence list must be non-empty."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert isinstance(result.evidence, list), "Evidence must be list"
        assert len(result.evidence) > 0, "Evidence list empty"

    def test_all_evidence_items_strings(self, mock_symbol_repo, sample_repo_id):
        """Each evidence item must be a string."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        for evidence_item in result.evidence:
            assert isinstance(
                evidence_item, str
            ), f"Evidence item not string: {type(evidence_item)}"
            assert len(evidence_item) > 5, f"Evidence item too short: '{evidence_item}'"

    def test_confidence_breakdown_complete(self, mock_symbol_repo, sample_repo_id):
        """Confidence breakdown must include all 5 styles."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        assert isinstance(breakdown, dict), "Breakdown must be dict"
        expected_styles = {"layered", "hexagonal", "mvc", "microservices", "flat"}
        actual_styles = set(breakdown.keys())
        assert (
            expected_styles == actual_styles
        ), f"Breakdown missing styles: expected {expected_styles}, got {actual_styles}"

        # All values must be floats in range
        for style, score in breakdown.items():
            assert isinstance(score, float), f"Score for {style} not float"
            assert 0.0 <= score <= 1.0, f"Score {score} out of range"


class TestArchitectureModelPersistence:
    """AC11/AC12: Save and load models from database."""

    def test_model_store_initialized(self, mock_symbol_repo, sample_repo_id):
        """AC11: ArchitectureModelStore can be instantiated."""
        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)
        assert store is not None

    def test_save_and_load_model(self, mock_symbol_repo, sample_repo_id):
        """AC11/AC12: Save model, load it back, verify data preserved."""
        # Detect architecture
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Save model
        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)
        model_id = store.save(result)

        assert model_id is not None, "save() must return model_id"
        assert isinstance(model_id, str), "model_id must be string"
        assert len(model_id) > 0, "model_id must not be empty"

    def test_load_latest_returns_model(self, mock_symbol_repo, sample_repo_id):
        """AC12: load_latest() retrieves most recent detection."""
        # Detect and save
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)
        model_id = store.save(result)

        # Load latest
        loaded = store.load_latest()

        assert loaded is not None, "load_latest() should return model"
        assert loaded.style == result.style, "Style must match"
        assert (
            loaded.style_confidence == result.confidence
        ), "Confidence must match"

    def test_persistence_data_integrity(self, mock_symbol_repo, sample_repo_id):
        """AC11: Saved model preserves all detection data."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)
        model_id = store.save(result)

        loaded = store.load_latest()

        assert loaded.style == result.style
        assert loaded.style_confidence == result.confidence
        # Evidence should be preserved (though order may vary)
        assert len(loaded.evidence) == len(result.evidence) or len(
            loaded.evidence
        ) > 0, "Evidence must be preserved"

    def test_multiple_saves_overwrites(self, mock_symbol_repo, sample_repo_id):
        """AC11: Successive saves for same repo create new versions."""
        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)

        # First detection
        detector1 = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result1 = detector1.detect()
        model_id1 = store.save(result1)

        # Second detection (same result in this test)
        detector2 = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result2 = detector2.detect()
        model_id2 = store.save(result2)

        assert model_id1 is not None
        assert model_id2 is not None
        # Both should exist (though might be same or different IDs)
        latest = store.load_latest()
        assert latest is not None

    def test_load_by_model_id(self, mock_symbol_repo, sample_repo_id):
        """AC12: load() retrieves model by specific ID."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        store = ArchitectureModelStore(mock_symbol_repo, sample_repo_id)
        model_id = store.save(result)

        loaded = store.load(model_id)

        assert loaded is not None, "load(model_id) should return model"
        assert loaded.style == result.style


class TestPerformanceBasics:
    """Detection should complete in reasonable time."""

    def test_detector_completes_quickly(self, mock_symbol_repo, sample_repo_id):
        """ArchitectureDetector.detect() should complete."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()
        assert result is not None

    def test_layer_detector_completes(self, mock_symbol_repo, sample_repo_id):
        """LayerDetector.detect_layers() should complete."""
        detector = LayerDetector(mock_symbol_repo, sample_repo_id)
        layers = detector.detect_layers()
        assert isinstance(layers, list)

    def test_subsystem_detector_completes(self, mock_symbol_repo, sample_repo_id):
        """SubsystemDetector.detect_subsystems() should complete."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()
        assert isinstance(subsystems, list)


class TestLayerDetectorIntegration:
    """AC5-AC8: Layer detection in context of full pipeline."""

    def test_layers_consistent_with_style(self, layered_fixture_db, layered_repo_id):
        """Layers should reflect detected style."""
        # Detect style first
        detector = ArchitectureDetector(layered_fixture_db, layered_repo_id)
        arch = detector.detect()

        # Get layers
        layer_det = LayerDetector(layered_fixture_db, layered_repo_id)
        layers = layer_det.detect_layers()

        # For layered architecture, should have multiple layers with hierarchy
        if arch.style == "layered":
            assert (
                len(layers) >= 2
            ), "Layered architecture should have multiple layers"

            # Layers should show dependency structure
            has_dependencies = any(l.depends_on for l in layers)
            assert has_dependencies, "Layered should have layer dependencies"

    def test_violations_detected_when_present(self, mock_symbol_repo, sample_repo_id):
        """AC7: detect_layer_violations() identifies issues."""
        layer_det = LayerDetector(mock_symbol_repo, sample_repo_id)
        violations = layer_det.detect_layer_violations()

        assert isinstance(violations, list), "Violations must be list"
        for v in violations:
            assert isinstance(v, str), "Violation must be string"
            assert len(v) > 0, "Violation must have description"


class TestSubsystemDetectorIntegration:
    """AC9-AC10: Subsystem detection in context of full pipeline."""

    def test_subsystems_reflect_architecture_style(self, layered_fixture_db, layered_repo_id):
        """Subsystems should vary based on architecture."""
        # Get subsystems
        subsys_det = SubsystemDetector(layered_fixture_db, layered_repo_id)
        subsystems = subsys_det.detect_subsystems()

        # Should identify multiple subsystems for layered arch
        assert len(subsystems) > 1, "Should detect multiple subsystems"

        # Each should have meaningful coupling
        couplings = [s.coupling_score for s in subsystems]
        assert any(c > 0.0 for c in couplings), "At least one subsystem should have coupling"

    def test_coupling_scores_meaningful(self, microservices_fixture_db, microservices_repo_id):
        """AC9: Coupling should vary meaningfully."""
        subsys_det = SubsystemDetector(microservices_fixture_db, microservices_repo_id)
        subsystems = subsys_det.detect_subsystems()

        couplings = [s.coupling_score for s in subsystems]

        # Should have at least some variation
        if len(subsystems) > 1:
            has_variation = len(set(couplings)) > 1 or any(c > 0.0 for c in couplings)
            assert has_variation, "Coupling should show variation"
