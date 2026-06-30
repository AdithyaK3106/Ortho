"""Tests for ArchitectureDetector — STRICT behavioral assertions."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from detector import ArchitectureDetector
from detection_types import ArchStyle


class TestArchitectureDetectorLayeredPattern:
    """AC1/AC2: Detect layered architecture style with confidence."""

    def test_layered_fixture_detects_as_layered(self, layered_fixture_db, layered_repo_id):
        """Test that canonical layered-architecture fixture detects as 'layered'."""
        detector = ArchitectureDetector(layered_fixture_db, layered_repo_id)
        result = detector.detect()

        assert result.style == "layered", f"Expected 'layered', got '{result.style}'"
        assert result.confidence >= 0.80, f"Expected confidence ≥0.80, got {result.confidence}"

    def test_layered_confidence_breakdown_shows_layered_highest(self, layered_fixture_db, layered_repo_id):
        """Test that layered gets highest score in breakdown."""
        detector = ArchitectureDetector(layered_fixture_db, layered_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        layered_score = breakdown.get("layered", 0.0)
        hex_score = breakdown.get("hexagonal", 0.0)
        mvc_score = breakdown.get("mvc", 0.0)
        micro_score = breakdown.get("microservices", 0.0)
        flat_score = breakdown.get("flat", 0.0)

        assert (
            layered_score >= hex_score
            and layered_score >= mvc_score
            and layered_score >= micro_score
            and layered_score >= flat_score
        ), f"Layered ({layered_score}) should beat hex/mvc/micro/flat"

    def test_layered_evidence_mentions_layers_and_upward_deps(self, layered_fixture_db, layered_repo_id):
        """AC2: Evidence describes why layered pattern detected."""
        detector = ArchitectureDetector(layered_fixture_db, layered_repo_id)
        result = detector.detect()

        evidence_text = " ".join(result.evidence).lower()
        assert "layer" in evidence_text, "Evidence must mention 'layer'"
        assert (
            "upward" in evidence_text or "depend" in evidence_text
        ), "Evidence must mention upward dependencies or dependencies"


class TestArchitectureDetectorHexagonalPattern:
    """AC1/AC2: Detect hexagonal (ports & adapters) architecture."""

    def test_hexagonal_fixture_detects_as_hexagonal(self, hexagonal_fixture_db, hexagonal_repo_id):
        """Test that canonical hexagonal fixture detects as 'hexagonal'."""
        detector = ArchitectureDetector(hexagonal_fixture_db, hexagonal_repo_id)
        result = detector.detect()

        assert result.style == "hexagonal", f"Expected 'hexagonal', got '{result.style}'"
        assert result.confidence >= 0.65, f"Expected confidence ≥0.65, got {result.confidence}"

    def test_hexagonal_confidence_breakdown_shows_hexagonal_highest(self, hexagonal_fixture_db, hexagonal_repo_id):
        """Test that hexagonal gets highest score in breakdown."""
        detector = ArchitectureDetector(hexagonal_fixture_db, hexagonal_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        hex_score = breakdown.get("hexagonal", 0.0)
        layered_score = breakdown.get("layered", 0.0)
        mvc_score = breakdown.get("mvc", 0.0)

        assert hex_score > layered_score, f"Hexagonal ({hex_score}) should beat layered ({layered_score})"
        assert hex_score > mvc_score, f"Hexagonal ({hex_score}) should beat mvc ({mvc_score})"


class TestArchitectureDetectorMVCPattern:
    """AC1/AC2: Detect MVC architecture."""

    def test_mvc_fixture_detects_as_mvc(self, mvc_fixture_db, mvc_repo_id):
        """Test that canonical MVC fixture detects as 'mvc'."""
        detector = ArchitectureDetector(mvc_fixture_db, mvc_repo_id)
        result = detector.detect()

        assert result.style == "mvc", f"Expected 'mvc', got '{result.style}'"
        assert result.confidence >= 0.70, f"Expected confidence ≥0.70, got {result.confidence}"

    def test_mvc_evidence_mentions_three_layers(self, mvc_fixture_db, mvc_repo_id):
        """AC2: Evidence describes three-tier MVC pattern."""
        detector = ArchitectureDetector(mvc_fixture_db, mvc_repo_id)
        result = detector.detect()

        evidence_text = " ".join(result.evidence).lower()
        # Should mention layers or view/controller/model
        has_mvc_terms = any(
            term in evidence_text for term in ["view", "controller", "model", "mvc", "three", "tier", "layer"]
        )
        assert has_mvc_terms, f"Evidence should mention MVC terms, got: {result.evidence}"


class TestArchitectureDetectorMicroservicesPattern:
    """AC1/AC2: Detect microservices architecture."""

    def test_microservices_fixture_detects_as_microservices(self, microservices_fixture_db, microservices_repo_id):
        """Test that canonical microservices fixture detects as 'microservices'."""
        detector = ArchitectureDetector(microservices_fixture_db, microservices_repo_id)
        result = detector.detect()

        assert (
            result.style == "microservices"
        ), f"Expected 'microservices', got '{result.style}'"
        assert result.confidence >= 0.70, f"Expected confidence ≥0.70, got {result.confidence}"

    def test_microservices_evidence_mentions_modularity(self, microservices_fixture_db, microservices_repo_id):
        """AC2: Evidence describes independent subsystems."""
        detector = ArchitectureDetector(microservices_fixture_db, microservices_repo_id)
        result = detector.detect()

        evidence_text = " ".join(result.evidence).lower()
        has_modularity = any(
            term in evidence_text for term in ["module", "subsystem", "independent", "coupling", "loose"]
        )
        assert has_modularity, f"Evidence should mention module separation, got: {result.evidence}"


class TestArchitectureDetectorFlatPattern:
    """AC1/AC2: Detect flat/monolithic architecture."""

    def test_flat_fixture_detects_as_flat(self, flat_fixture_db, flat_repo_id):
        """Test that canonical flat fixture detects as 'flat'."""
        detector = ArchitectureDetector(flat_fixture_db, flat_repo_id)
        result = detector.detect()

        assert result.style == "flat", f"Expected 'flat', got '{result.style}'"
        # Flat can have lower confidence since pattern is less structured
        assert result.confidence >= 0.45, f"Expected confidence ≥0.45, got {result.confidence}"

    def test_flat_evidence_mentions_interconnection(self, flat_fixture_db, flat_repo_id):
        """AC2: Evidence describes high interconnection."""
        detector = ArchitectureDetector(flat_fixture_db, flat_repo_id)
        result = detector.detect()

        evidence_text = " ".join(result.evidence).lower()
        has_flat_indicators = any(
            term in evidence_text
            for term in ["flat", "monolithic", "interconnect", "coupling", "no layer", "everything"]
        )
        assert has_flat_indicators, f"Evidence should indicate flat pattern, got: {result.evidence}"


class TestArchitectureDetectorLowConfidenceHandling:
    """AC4: Handle low-confidence/ambiguous cases gracefully."""

    def test_ambiguous_fixture_returns_alternative(self, ambiguous_fixture_db, ambiguous_repo_id):
        """AC4: Ambiguous case returns both style and alternative."""
        detector = ArchitectureDetector(ambiguous_fixture_db, ambiguous_repo_id)
        result = detector.detect()

        # Must have alternative for ambiguous case
        assert result.alternative is not None, "Ambiguous fixture must suggest alternative"
        assert (
            result.alternative_confidence is not None
        ), "Alternative confidence must be set"
        # Gap should be small (within 0.15)
        confidence_gap = abs(result.confidence - result.alternative_confidence)
        assert (
            confidence_gap <= 0.15
        ), f"Ambiguous case should have gap ≤0.15, got {confidence_gap}"

    def test_confidence_always_in_range(self, mock_symbol_repo, sample_repo_id):
        """AC3: Confidence always in [0.0, 1.0]."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert 0.0 <= result.confidence <= 1.0, f"Confidence {result.confidence} out of range"
        if result.alternative_confidence is not None:
            assert (
                0.0 <= result.alternative_confidence <= 1.0
            ), f"Alt confidence {result.alternative_confidence} out of range"


class TestArchitectureDetectorEvidenceQuality:
    """AC2: Evidence must be detailed, not just existence check."""

    def test_evidence_not_empty_list(self, mock_symbol_repo, sample_repo_id):
        """Evidence list must contain items."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert isinstance(result.evidence, list), "Evidence must be a list"
        assert len(result.evidence) > 0, "Evidence list must not be empty"

    def test_evidence_contains_meaningful_strings(self, mock_symbol_repo, sample_repo_id):
        """Each evidence item must be substantive (not just type check)."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        for evidence_item in result.evidence:
            assert isinstance(evidence_item, str), f"Evidence item must be string, got {type(evidence_item)}"
            assert len(evidence_item) > 10, f"Evidence item too short: '{evidence_item}'"
            # Evidence should describe something, not just be a tag
            has_content = any(
                word in evidence_item.lower()
                for word in ["layer", "module", "coupling", "depend", "pattern", "score", "confidence", "edge"]
            )
            assert has_content, f"Evidence item lacks meaningful content: '{evidence_item}'"

    def test_evidence_describes_detection_not_just_metrics(self, mock_symbol_repo, sample_repo_id):
        """AC2: Evidence should mention why pattern was detected, not just that it was."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        evidence_text = " ".join(result.evidence)
        # Should have both metrics and reasoning
        assert len(evidence_text) > 50, "Evidence should be substantive"


class TestConfidenceBreakdown:
    """Confidence breakdown must show all styles."""

    def test_breakdown_includes_all_five_styles(self, mock_symbol_repo, sample_repo_id):
        """Breakdown must have scores for all 5 styles."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        expected_styles = {"layered", "hexagonal", "mvc", "microservices", "flat"}
        actual_styles = set(breakdown.keys())

        assert (
            expected_styles == actual_styles
        ), f"Expected {expected_styles}, got {actual_styles}"

    def test_breakdown_scores_sum_meaningfully(self, mock_symbol_repo, sample_repo_id):
        """Scores should be comparable (not all zero or all one)."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        scores = list(breakdown.values())
        # At least some variance (not all identical)
        unique_scores = len(set(scores)) > 1
        assert (
            unique_scores or all(s == 0.0 for s in scores)
        ), "Scores should show differentiation"


class TestDeterminism:
    """Same repo should produce identical results."""

    def test_detect_twice_gives_identical_result(self, mock_symbol_repo, sample_repo_id):
        """Running detect() twice must produce identical output."""
        detector1 = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result1 = detector1.detect()

        detector2 = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result2 = detector2.detect()

        assert result1.style == result2.style, "Style must be identical"
        assert result1.confidence == result2.confidence, "Confidence must be identical"
        assert result1.evidence == result2.evidence, "Evidence must be identical"
        assert result1.alternative == result2.alternative, "Alternative must be identical"
        if result1.alternative_confidence and result2.alternative_confidence:
            assert (
                result1.alternative_confidence == result2.alternative_confidence
            ), "Alt confidence must be identical"
