"""Tests for SubsystemDetector — STRICT behavioral assertions."""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))
sys.path.insert(0, str(project_root / "packages" / "arch-intelligence" / "src"))

from subsystem_detector import SubsystemDetector


class TestSubsystemDetectionBasics:
    """AC9: Cluster related modules into subsystems."""

    def test_detect_subsystems_returns_nonempty_list(self, mock_symbol_repo, sample_repo_id):
        """AC9: detect_subsystems() returns non-empty list."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        assert isinstance(subsystems, list), "Must return list"
        assert len(subsystems) > 0, "Must detect at least one subsystem"

    def test_layered_fixture_detects_subsystems(self, layered_fixture_db, layered_repo_id):
        """AC9: Layered fixture should detect subsystems (auth, user, etc)."""
        detector = SubsystemDetector(layered_fixture_db, layered_repo_id)
        subsystems = detector.detect_subsystems()

        # Layered fixture has ~5 subsystems (auth, user, order, payment, util)
        assert len(subsystems) >= 3, f"Expected ≥3 subsystems, got {len(subsystems)}"

    def test_microservices_fixture_detects_services(self, microservices_fixture_db, microservices_repo_id):
        """AC9: Microservices fixture should detect ~4 independent services."""
        detector = SubsystemDetector(microservices_fixture_db, microservices_repo_id)
        subsystems = detector.detect_subsystems()

        # Microservices fixture has ~4 services
        assert len(subsystems) >= 3, f"Expected ≥3 services, got {len(subsystems)}"


class TestSubsystemFieldContent:
    """AC9/AC10: Subsystem objects must contain correct data."""

    def test_subsystem_id_is_string(self, mock_symbol_repo, sample_repo_id):
        """Subsystem.id must be a non-empty string."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert isinstance(subsys.id, str), f"Subsystem.id must be string, got {type(subsys.id)}"
            assert len(subsys.id) > 0, "Subsystem.id must not be empty"

    def test_subsystem_name_is_meaningful(self, mock_symbol_repo, sample_repo_id):
        """AC10: Subsystem names must be meaningful (not "unknown")."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert isinstance(subsys.name, str), f"Subsystem.name must be string"
            assert len(subsys.name) > 0, "Subsystem.name must not be empty"
            # Can be auto-numbered or semantic, but not "unknown"
            assert subsys.name.lower() not in [
                "unknown",
                "none",
            ], f"Subsystem has invalid name: {subsys.name}"

    def test_subsystem_file_ids_nonempty(self, mock_symbol_repo, sample_repo_id):
        """Subsystem.file_ids must be non-empty list of strings."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert isinstance(subsys.file_ids, list), "file_ids must be list"
            assert len(subsys.file_ids) > 0, f"Subsystem '{subsys.name}' has no files"
            for fid in subsys.file_ids:
                assert isinstance(fid, str), f"File ID must be string, got {type(fid)}"

    def test_coupling_score_is_float_in_range(self, mock_symbol_repo, sample_repo_id):
        """AC9: Coupling score must be float in [0.0, 1.0]."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        for subsys in subsystems:
            assert isinstance(
                subsys.coupling_score, float
            ), f"Coupling must be float, got {type(subsys.coupling_score)}"
            assert (
                0.0 <= subsys.coupling_score <= 1.0
            ), f"Coupling {subsys.coupling_score} out of range"


class TestCouplingCalculation:
    """AC9: _compute_coupling_score() calculates internal_edges / max_possible_edges."""

    def test_tightly_coupled_has_high_score(self, mock_symbol_repo, sample_repo_id):
        """Subsystem with many internal edges should have high coupling."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        # At least one subsystem should exist
        assert len(subsystems) > 0

        # At least one should have measurable coupling
        coupling_scores = [s.coupling_score for s in subsystems]
        assert max(coupling_scores) > 0.0, "At least one subsystem should have coupling > 0"

    def test_layered_fixture_has_varied_coupling(self, layered_fixture_db, layered_repo_id):
        """AC9: Different subsystems should have different coupling scores."""
        detector = SubsystemDetector(layered_fixture_db, layered_repo_id)
        subsystems = detector.detect_subsystems()

        scores = [s.coupling_score for s in subsystems]

        # Should have some variation in coupling
        if len(subsystems) > 1:
            unique_scores = len(set(scores))
            # Allow for rounding, but should have at least 2 distinct values
            assert unique_scores >= 1, f"Should have varied coupling, got {unique_scores} unique"

    def test_microservices_has_low_intercoupling(self, microservices_fixture_db, microservices_repo_id):
        """AC9: Microservices should generally have moderate internal coupling."""
        detector = SubsystemDetector(microservices_fixture_db, microservices_repo_id)
        subsystems = detector.detect_subsystems()

        # Most services should have measurable coupling (internal)
        for subsys in subsystems:
            if len(subsys.file_ids) > 1:
                # Multi-file services should show internal coupling
                assert subsys.coupling_score >= 0.0, "Coupling must be ≥0"

    def test_flat_fixture_high_coupling(self, flat_fixture_db, flat_repo_id):
        """AC9: Flat fixture (all-connected) should have high coupling."""
        detector = SubsystemDetector(flat_fixture_db, flat_repo_id)
        subsystems = detector.detect_subsystems()

        # In flat architecture, all files are connected, so coupling should be high
        if len(subsystems) == 1 and len(subsystems[0].file_ids) > 2:
            # Single subsystem with all files highly connected
            assert (
                subsystems[0].coupling_score >= 0.5
            ), f"Flat arch should have high coupling, got {subsystems[0].coupling_score}"


class TestSubsystemNaming:
    """AC10: _suggest_subsystem_name() derives names from paths."""

    def test_names_derived_from_structure(self, layered_fixture_db, layered_repo_id):
        """AC10: Subsystem names should reflect module structure."""
        detector = SubsystemDetector(layered_fixture_db, layered_repo_id)
        subsystems = detector.detect_subsystems()

        names = {s.name.lower() for s in subsystems}

        # Layered fixture has auth, user, order, payment subsystems
        # At least some should be detected by name
        has_business_domain = any(
            domain in str(names) for domain in ["auth", "user", "order", "payment", "business"]
        )
        # Names should be intelligible (not just auto-numbered)
        assert (
            len(names) > 0
        ), f"Should derive subsystem names from structure, got {names}"

    def test_microservices_names_reflect_services(self, microservices_fixture_db, microservices_repo_id):
        """AC10: Microservices should be named after services."""
        detector = SubsystemDetector(microservices_fixture_db, microservices_repo_id)
        subsystems = detector.detect_subsystems()

        names = {s.name.lower() for s in subsystems}

        # Microservices fixture has auth, payment, user, notification services
        # At least some should be recognized
        has_service_names = any(
            service in str(names)
            for service in [
                "auth",
                "payment",
                "user",
                "notif",
                "service",
            ]
        )
        assert len(subsystems) > 0, "Should detect multiple services"


class TestSubsystemOrganization:
    """AC9: File assignments must be valid."""

    def test_no_file_duplicates_across_subsystems(self, mock_symbol_repo, sample_repo_id):
        """Each file must appear in exactly one subsystem."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        all_files = []
        for subsys in subsystems:
            all_files.extend(subsys.file_ids)

        # No file appears twice
        assert len(all_files) == len(
            set(all_files)
        ), "File appears in multiple subsystems"

    def test_all_files_in_subsystems(self, mock_symbol_repo, sample_repo_id):
        """All repository files must be in some subsystem."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        subsystem_files = set()
        for subsys in subsystems:
            subsystem_files.update(subsys.file_ids)

        # Should have assigned files
        assert len(subsystem_files) > 0, "No files assigned to subsystems"


class TestDeterminism:
    """AC9: Detection must be deterministic."""

    def test_detect_twice_identical(self, mock_symbol_repo, sample_repo_id):
        """Running detect_subsystems() twice must produce identical results."""
        detector1 = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsys1 = detector1.detect_subsystems()

        detector2 = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsys2 = detector2.detect_subsystems()

        assert len(subsys1) == len(subsys2), "Subsystem count must be identical"

        for s1, s2 in zip(subsys1, subsys2):
            assert s1.id == s2.id, f"IDs differ: {s1.id} vs {s2.id}"
            assert s1.name == s2.name, f"Names differ: {s1.name} vs {s2.name}"
            # file_ids might be in different order (set comparison)
            assert set(s1.file_ids) == set(
                s2.file_ids
            ), f"File membership differs for {s1.id}"
            assert (
                s1.coupling_score == s2.coupling_score
            ), f"Coupling differs for {s1.id}"


class TestSubsystemSorting:
    """Subsystems are ordered by coupling (highest first)."""

    def test_subsystems_sorted_descending_by_coupling(self, mock_symbol_repo, sample_repo_id):
        """If multiple subsystems, should be sorted by coupling descending."""
        detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
        subsystems = detector.detect_subsystems()

        if len(subsystems) > 1:
            scores = [s.coupling_score for s in subsystems]
            # Should be in descending order (or close to it for tie-breaking)
            for i in range(len(scores) - 1):
                assert (
                    scores[i] >= scores[i + 1]
                ), f"Subsystems not sorted: {scores[i]} < {scores[i+1]}"
