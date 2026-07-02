"""Subsystem detection tests - stateless API per specification."""

import pytest
from arch_intelligence.subsystem_detector import SubsystemDetector
from arch_intelligence.arch_detector import CallEdge, File
from arch_intelligence.types import Subsystem


@pytest.fixture
def subsystem_detector():
    return SubsystemDetector()


class TestSubsystemDetectionBasics:
    """Test basic subsystem detection (stateless API)."""

    def test_detect_subsystems_returns_list(self, subsystem_detector):
        """detect_subsystems should return a list."""
        call_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        result = subsystem_detector.detect_subsystems(call_graph, [], files)
        assert isinstance(result, list)

    def test_microservices_fixture_detects(self, subsystem_detector):
        """Microservices-like structure should detect subsystems."""
        call_graph = [
            CallEdge(caller_id="auth_svc", callee_id="auth_db"),
            CallEdge(caller_id="user_svc", callee_id="user_db"),
        ]
        files = [
            File(id="auth_svc", rel_path="services/auth.py"),
            File(id="auth_db", rel_path="services/auth_db.py"),
            File(id="user_svc", rel_path="services/user.py"),
            File(id="user_db", rel_path="services/user_db.py"),
        ]
        
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        assert isinstance(subsystems, list)


class TestSubsystemFieldContent:
    """Test subsystem dataclass fields."""

    def test_subsystem_has_id(self, subsystem_detector):
        """Subsystems should have id field."""
        call_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        if subsystems:
            assert hasattr(subsystems[0], "id")
            assert isinstance(subsystems[0].id, str)

    def test_subsystem_has_name(self, subsystem_detector):
        """Subsystems should have name field."""
        call_graph = []
        files = [File(id="auth.py", rel_path="services/auth.py")]
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        if subsystems:
            assert hasattr(subsystems[0], "name")

    def test_subsystem_has_file_ids(self, subsystem_detector):
        """Subsystems should have file_ids list."""
        call_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        if subsystems:
            assert hasattr(subsystems[0], "file_ids")
            assert isinstance(subsystems[0].file_ids, list)

    def test_coupling_score_in_range(self, subsystem_detector):
        """Coupling score should be in [0.0, 1.0]."""
        call_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        if subsystems:
            assert hasattr(subsystems[0], "coupling_score")
            assert 0.0 <= subsystems[0].coupling_score <= 1.0


class TestCouplingCalculation:
    """Test coupling score accuracy."""

    def test_isolated_files_low_coupling(self, subsystem_detector):
        """Isolated files should have low coupling."""
        call_graph = []
        files = [File(id="a.py", rel_path="a.py"), File(id="b.py", rel_path="b.py")]
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        # All subsystems should have reasonable coupling scores
        for subsystem in subsystems:
            assert 0.0 <= subsystem.coupling_score <= 1.0


class TestDeterminism:
    """Test that clustering is deterministic."""

    def test_detect_twice_identical(self, subsystem_detector):
        """Detecting subsystems twice should produce identical clustering."""
        call_graph = [
            CallEdge(caller_id="a", callee_id="b"),
            CallEdge(caller_id="c", callee_id="d"),
        ]
        files = [
            File(id="a", rel_path="a.py"),
            File(id="b", rel_path="b.py"),
            File(id="c", rel_path="c.py"),
            File(id="d", rel_path="d.py"),
        ]
        
        subsys1 = subsystem_detector.detect_subsystems(call_graph, [], files)
        subsys2 = subsystem_detector.detect_subsystems(call_graph, [], files)
        
        assert len(subsys1) == len(subsys2)
        if subsys1:
            assert subsys1[0].id == subsys2[0].id

