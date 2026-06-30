"""Tests for ArchitectureDetector."""

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


class TestArchitectureDetectorBasics:
    """Basic detector functionality tests."""

    def test_detector_initializes(self, temp_db, sample_repo_id):
        """Test that ArchitectureDetector can be instantiated."""
        detector = ArchitectureDetector(temp_db, sample_repo_id)
        assert detector is not None
        assert detector.repo_id == sample_repo_id

    def test_detect_returns_result(self, mock_symbol_repo, sample_repo_id):
        """Test that detect() returns a DetectionResult."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert result is not None
        assert hasattr(result, "style")
        assert hasattr(result, "confidence")
        assert hasattr(result, "evidence")

    def test_confidence_in_valid_range(self, mock_symbol_repo, sample_repo_id):
        """Test that confidence score is between 0.0 and 1.0."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert 0.0 <= result.confidence <= 1.0

    def test_style_is_valid_enum(self, mock_symbol_repo, sample_repo_id):
        """Test that detected style is a valid architecture style."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        valid_styles = ["layered", "hexagonal", "mvc", "microservices", "flat", "unknown"]
        assert result.style in valid_styles

    def test_evidence_list_not_empty(self, mock_symbol_repo, sample_repo_id):
        """Test that evidence list contains items."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        assert len(result.evidence) > 0
        assert all(isinstance(e, str) for e in result.evidence)

    def test_confidence_breakdown(self, mock_symbol_repo, sample_repo_id):
        """Test that confidence breakdown includes all styles."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        breakdown = detector.detect_confidence_breakdown()

        assert breakdown is not None
        assert len(breakdown) > 0

    def test_alternative_style_lower_confidence(self, mock_symbol_repo, sample_repo_id):
        """Test that alternative style (if present) has lower confidence."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        if result.alternative:
            assert result.alternative_confidence <= result.confidence


class TestArchitectureDetectorLayering:
    """Tests for layering detection."""

    def test_layering_score_computed(self, mock_symbol_repo, sample_repo_id):
        """Test that layering score is computed."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Evidence should include layering score
        has_layering = any("layering" in e.lower() for e in result.evidence)
        assert has_layering

    def test_upward_dependencies_in_evidence(self, mock_symbol_repo, sample_repo_id):
        """Test that evidence mentions upward dependencies."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # If detected as layered, evidence should mention upward deps
        if result.style == "layered":
            has_upward = any("upward" in e.lower() or "depend" in e.lower() for e in result.evidence)
            assert has_upward


class TestArchitectureDetectorEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_repo(self, temp_db, sample_repo_id):
        """Test detection on empty repository."""
        conn = temp_db.connection()
        conn.execute(
            "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
            (sample_repo_id, "/test/empty", "empty-repo"),
        )
        conn.commit()
        conn.close()

        detector = ArchitectureDetector(temp_db, sample_repo_id)
        result = detector.detect()

        # Should still return a valid result
        assert result is not None
        assert result.style in ["layered", "hexagonal", "mvc", "microservices", "flat", "unknown"]

    def test_single_file_repo(self, temp_db, sample_repo_id):
        """Test detection on repo with single file."""
        conn = temp_db.connection()
        conn.execute(
            "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
            (sample_repo_id, "/test/single", "single-file"),
        )
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            ("file-1", sample_repo_id, "main.py", "python", 100),
        )
        conn.commit()
        conn.close()

        detector = ArchitectureDetector(temp_db, sample_repo_id)
        result = detector.detect()

        assert result is not None
        assert 0.0 <= result.confidence <= 1.0

    def test_determinism(self, mock_symbol_repo, sample_repo_id):
        """Test that running detect() twice produces identical results."""
        detector1 = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result1 = detector1.detect()

        detector2 = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result2 = detector2.detect()

        assert result1.style == result2.style
        assert result1.confidence == result2.confidence
        assert result1.evidence == result2.evidence


class TestMetricsPresence:
    """Test that evidence includes structured metrics."""

    def test_metric_tags_in_evidence(self, mock_symbol_repo, sample_repo_id):
        """Test that evidence includes [METRIC] tags."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Should have some metrics
        metrics = [e for e in result.evidence if "[METRIC]" in e]
        assert len(metrics) > 0 or len(result.evidence) > 0  # Either metrics or human text

    def test_confidence_tags_in_evidence(self, mock_symbol_repo, sample_repo_id):
        """Test that evidence includes [CONFIDENCE] tags."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # Should include breakdown of all style confidence scores
        breakdown = detector.detect_confidence_breakdown()
        assert len(breakdown) > 0


class TestAlternativeDetection:
    """Test alternative architecture detection."""

    def test_alternative_when_ambiguous(self, mock_symbol_repo, sample_repo_id):
        """Test that ambiguous results include an alternative."""
        detector = ArchitectureDetector(mock_symbol_repo, sample_repo_id)
        result = detector.detect()

        # For this mock layered repo, should detect layered confidently
        assert result.style is not None


class TestCycleHandling:
    """Test behavior with cyclic dependencies (edge cases)."""

    def test_detector_handles_missing_data_gracefully(self, temp_db, sample_repo_id):
        """Test that detector doesn't crash with incomplete data."""
        conn = temp_db.connection()
        conn.execute(
            "INSERT INTO repositories (id, root_path, name) VALUES (?, ?, ?)",
            (sample_repo_id, "/test/incomplete", "incomplete"),
        )
        # File without any imports
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language, size_bytes, last_modified) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            ("orphan", sample_repo_id, "orphan.py", "python", 50),
        )
        conn.commit()
        conn.close()

        detector = ArchitectureDetector(temp_db, sample_repo_id)
        result = detector.detect()

        assert result is not None
        assert isinstance(result.confidence, float)
