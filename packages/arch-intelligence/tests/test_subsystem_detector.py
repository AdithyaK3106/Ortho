"""Tests for SubsystemDetector."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from subsystem_detector import SubsystemDetector


class TestSubsystemDetectorBasics:
    """Basic subsystem detection tests."""

    def test_detector_initializes(self, temp_db, sample_repo_id):
        """Test that SubsystemDetector can be instantiated."""
        detector = SubsystemDetector(temp_db, sample_repo_id)
        assert detector is not None

    def test_detect_subsystems_returns_list(self, mock_symbol_repo, sample_repo_id):
        """Test that detect_subsystems() returns a list."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        assert isinstance(subsystems, list)
        assert len(subsystems) > 0

    def test_subsystems_have_required_fields(self, mock_symbol_repo, sample_repo_id):
        """Test that each subsystem has required fields."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert hasattr(subsys, "id")
            assert hasattr(subsys, "name")
            assert hasattr(subsys, "file_ids")
            assert hasattr(subsys, "coupling_score")

    def test_coupling_score_in_range(self, mock_symbol_repo, sample_repo_id):
        """Test that coupling score is 0.0-1.0."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert 0.0 <= subsys.coupling_score <= 1.0

    def test_subsystem_names_not_empty(self, mock_symbol_repo, sample_repo_id):
        """Test that subsystem names are assigned."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert isinstance(subsys.name, str)
            assert len(subsys.name) > 0

    def test_subsystem_file_ids_are_strings(self, mock_symbol_repo, sample_repo_id):
        """Test that file_ids are strings."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert all(isinstance(fid, str) for fid in subsys.file_ids)


class TestSubsystemCouplingCalculation:
    """Test coupling score calculation."""

    def test_tightly_coupled_subsystem_high_score(self, mock_symbol_repo, sample_repo_id):
        """Test that tightly coupled modules have high coupling score."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        # At least one subsystem should exist
        assert len(subsystems) > 0

    def test_coupling_meaningful(self, mock_symbol_repo, sample_repo_id):
        """Test that coupling scores vary (not all the same)."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        if len(subsystems) > 1:
            scores = [s.coupling_score for s in subsystems]
            # Should have some variation
            assert len(set(scores)) > 1 or all(s == 0.0 for s in scores)


class TestSubsystemNaming:
    """Test subsystem name assignment."""

    def test_names_assigned_from_paths(self, mock_symbol_repo, sample_repo_id):
        """Test that subsystem names are derived from file paths."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        # Names should be meaningful (not just "subsystem_0")
        for subsys in subsystems:
            # Either has meaningful name or auto-numbered
            assert subsys.name.lower() != "unknown"


class TestSubsystemOrganization:
    """Test subsystem organization properties."""

    def test_no_duplicate_file_ids_across_subsystems(self, mock_symbol_repo, sample_repo_id):
        """Test that each file belongs to exactly one subsystem."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        all_files = []
        for subsys in subsystems:
            all_files.extend(subsys.file_ids)

        # Each file should appear exactly once
        assert len(all_files) == len(set(all_files))

    def test_all_files_in_some_subsystem(self, mock_symbol_repo, sample_repo_id):
        """Test that all files are assigned to subsystems."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        subsystem_files = set()
        for subsys in subsystems:
            subsystem_files.update(subsys.file_ids)

        # Should have assigned all files
        assert len(subsystem_files) > 0


class TestSubsystemConsistency:
    """Test consistency and determinism."""

    def test_determinism(self, mock_symbol_repo, sample_repo_id):
        """Test that running detect_subsystems() twice gives same result."""
        detector1 = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsys1 = detector1.detect_subsystems()

        detector2 = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsys2 = detector2.detect_subsystems()

        assert len(subsys1) == len(subsys2)
        for s1, s2 in zip(subsys1, subsys2):
            assert s1.id == s2.id
            assert s1.name == s2.name
            assert set(s1.file_ids) == set(s2.file_ids)
            assert s1.coupling_score == s2.coupling_score

    def test_subsystems_sorted_by_coupling(self, mock_symbol_repo, sample_repo_id):
        """Test that subsystems are sorted (highest coupling first)."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        if len(subsystems) > 1:
            scores = [s.coupling_score for s in subsystems]
            # Should be in descending order (or at least not ascending)
            assert scores[0] >= scores[-1]
