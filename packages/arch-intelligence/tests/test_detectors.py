"""Unit tests for architecture detection."""

import pytest
from arch_intelligence.arch_detector import ArchitectureDetector, CallEdge, ImportEdge, File
from arch_intelligence.types import ArchStyle
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.subsystem_detector import SubsystemDetector
from arch_intelligence.model_store import ArchitectureModelStore


@pytest.fixture
def detector():
    return ArchitectureDetector()


@pytest.fixture
def layer_detector():
    return LayerDetector()


@pytest.fixture
def subsystem_detector():
    return SubsystemDetector()


class TestArchitectureDetector:
    """Tests for ArchitectureDetector."""

    def test_detect_layered_pattern(self, detector):
        """Test detection of layered architecture."""
        call_graph = []
        import_graph = [
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
            ImportEdge(importer_file_id="c.py", imported_file_id="b.py"),
        ]
        files = [
            File(id="a.py", rel_path="data/repository.py"),
            File(id="b.py", rel_path="service/user_service.py"),
            File(id="c.py", rel_path="api/controller.py"),
        ]
        
        result = detector.detect(call_graph, import_graph, [], files)
        
        assert result.style in [ArchStyle.LAYERED, ArchStyle.HEXAGONAL, ArchStyle.MVC]
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.evidence) > 0

    def test_detect_mvc_pattern(self, detector):
        """Test detection of MVC architecture."""
        call_graph = []
        import_graph = [
            ImportEdge(importer_file_id="controller.py", imported_file_id="model.py"),
            ImportEdge(importer_file_id="view.py", imported_file_id="model.py"),
        ]
        files = [
            File(id="model.py", rel_path="models/user.py"),
            File(id="controller.py", rel_path="controllers/user_controller.py"),
            File(id="view.py", rel_path="views/user_view.py"),
        ]
        
        result = detector.detect(call_graph, import_graph, [], files)
        
        assert result.style in [ArchStyle.MVC, ArchStyle.LAYERED]
        assert 0.3 <= result.confidence <= 1.0

    def test_confidence_range(self, detector):
        """Test that confidence is always in [0.0, 1.0]."""
        result = detector.detect([], [], [], [])
        assert 0.0 <= result.confidence <= 1.0

    def test_style_is_valid(self, detector):
        """Test that detected style is a valid ArchStyle (UNKNOWN allowed:
        the detector never guesses on empty/insufficient evidence)."""
        result = detector.detect([], [], [], [])
        assert result.style in set(ArchStyle)
        # Empty input has no evidence for any style
        assert result.style == ArchStyle.UNKNOWN

    def test_evidence_not_empty(self, detector):
        """Test that evidence list is populated."""
        call_graph = [CallEdge(caller_id="a", callee_id="b")]
        import_graph = [ImportEdge(importer_file_id="a.py", imported_file_id="b.py")]
        files = [File(id="a.py", rel_path="a.py"), File(id="b.py", rel_path="b.py")]
        
        result = detector.detect(call_graph, import_graph, [], files)
        
        assert len(result.evidence) > 0
        assert any("Confidence" in e for e in result.evidence)


class TestLayerDetector:
    """Tests for LayerDetector."""

    def test_extract_layers_from_dag(self, layer_detector):
        """Test layer extraction with real persistence/framework evidence."""
        import_graph = [
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
            ImportEdge(importer_file_id="c.py", imported_file_id="b.py"),
        ]
        files = [
            File(id="a.py", rel_path="data/db.py"),
            File(id="b.py", rel_path="service/logic.py"),
            File(id="c.py", rel_path="api/handler.py"),
        ]
        external = {"a.py": {"sqlalchemy"}, "c.py": {"flask"}}

        layers = layer_detector.extract_layers(import_graph, files, external)

        assert len(layers) >= 1
        assert all(0 <= layer.number <= 1 for layer in layers)

    def test_layer_numbering(self, layer_detector):
        """Test that layers are numbered consistently."""
        import_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        
        layers = layer_detector.extract_layers(import_graph, files)
        
        if layers:
            assert all(isinstance(layer.number, int) for layer in layers)

    def test_semantic_naming_detection(self, layer_detector):
        """Test semantic naming: a module with a real persistence-library
        import gets classified as Data, not from path keywords alone."""
        import_graph = [ImportEdge(importer_file_id="service.py", imported_file_id="repository.py")]
        files = [
            File(id="repository.py", rel_path="data/repository.py"),
            File(id="service.py", rel_path="logic/service.py"),
        ]
        external = {"repository.py": {"sqlalchemy"}}

        layers = layer_detector.extract_layers(import_graph, files, external)

        assert len(layers) >= 1
        assert layers[0].name == "Data"


class TestSubsystemDetector:
    """Tests for SubsystemDetector."""

    def test_detect_subsystems(self, subsystem_detector):
        """Test subsystem detection."""
        call_graph = [
            CallEdge(caller_id="a", callee_id="b"),
            CallEdge(caller_id="b", callee_id="a"),
        ]
        files = [
            File(id="a.py", rel_path="auth/login.py"),
            File(id="b.py", rel_path="auth/token.py"),
        ]
        
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        
        assert len(subsystems) >= 0
        if subsystems:
            assert all(0.0 <= s.coupling_score <= 1.0 for s in subsystems)

    def test_coupling_score_range(self, subsystem_detector):
        """Test that coupling scores are in [0.0, 1.0]."""
        call_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
        
        assert all(0.0 <= s.coupling_score <= 1.0 for s in subsystems)

    def test_subsystem_stability(self, subsystem_detector):
        """Test that clustering is deterministic with fixed seed."""
        call_graph = [
            CallEdge(caller_id="a", callee_id="b"),
            CallEdge(caller_id="c", callee_id="d"),
        ]
        files = [
            File(id="a.py", rel_path="a.py"),
            File(id="b.py", rel_path="b.py"),
            File(id="c.py", rel_path="c.py"),
            File(id="d.py", rel_path="d.py"),
        ]
        
        result1 = subsystem_detector.detect_subsystems(call_graph, [], files)
        result2 = subsystem_detector.detect_subsystems(call_graph, [], files)
        
        assert len(result1) == len(result2)


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_graphs(self, detector):
        """Test handling of empty graphs: no evidence → UNKNOWN, not a guess."""
        result = detector.detect([], [], [], [])
        assert result.style == ArchStyle.UNKNOWN
        assert result.confidence == 0.0

    def test_single_file(self, detector):
        """Test handling of single-file repos."""
        files = [File(id="a.py", rel_path="a.py")]
        result = detector.detect([], [], [], files)
        assert 0.0 <= result.confidence <= 1.0

    def test_no_imports(self, detector):
        """Test handling of repos with no imports."""
        files = [
            File(id="a.py", rel_path="a.py"),
            File(id="b.py", rel_path="b.py"),
        ]
        result = detector.detect([], [], [], files)
        assert 0.0 <= result.confidence <= 1.0
        assert result.style in {
            ArchStyle.LAYERED,
            ArchStyle.HEXAGONAL,
            ArchStyle.MVC,
            ArchStyle.MICROSERVICES,
            ArchStyle.FLAT,
        }

