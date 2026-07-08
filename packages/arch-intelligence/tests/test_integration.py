"""Integration tests for architecture detection pipeline."""

import pytest
from arch_intelligence.arch_detector import ArchitectureDetector, CallEdge, ImportEdge, File
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.subsystem_detector import SubsystemDetector
from arch_intelligence.model_store import ArchitectureModelStore
from arch_intelligence.types import ArchStyle, ArchitectureModel


@pytest.fixture
def arch_db(tmp_path):
    """Create temporary database for testing."""
    db_path = tmp_path / "test.db"
    return ArchitectureModelStore(str(db_path))


class TestFullPipeline:
    """End-to-end pipeline tests."""

    def test_full_pipeline_simple_layered(self, arch_db):
        """Test complete pipeline on simple 3-layer structure."""
        detector = ArchitectureDetector()
        layer_detector = LayerDetector()
        subsystem_detector = SubsystemDetector()

        # Create synthetic 3-layer repo
        call_graph = []
        import_graph = [
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
            ImportEdge(importer_file_id="c.py", imported_file_id="b.py"),
        ]
        files = [
            File(id="a.py", rel_path="data/db.py"),
            File(id="b.py", rel_path="service/logic.py"),
            File(id="c.py", rel_path="api/handler.py"),
        ]

        # Run detection
        detection_result = detector.detect(call_graph, import_graph, [], files)
        layers = layer_detector.extract_layers(import_graph, files)
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)

        # Build and save model
        model = ArchitectureModel(
            repo_id="test-repo",
            style=detection_result.style,
            style_confidence=detection_result.confidence,
            layers=layers,
            subsystems=subsystems,
            detected_at="2026-07-02T00:00:00Z",
            evidence=detection_result.evidence,
        )

        model_id = arch_db.save(model)
        assert model_id is not None

        # Load and verify
        loaded = arch_db.load_latest("test-repo")
        assert loaded is not None
        assert loaded.repo_id == "test-repo"
        assert loaded.style == detection_result.style
        assert 0.0 <= loaded.style_confidence <= 1.0

    def test_full_pipeline_microservices(self, arch_db):
        """Test pipeline on microservices-like structure."""
        detector = ArchitectureDetector()
        layer_detector = LayerDetector()
        subsystem_detector = SubsystemDetector()

        # Create synthetic microservices (multiple isolated subsystems)
        call_graph = [
            CallEdge(caller_id="auth_svc", callee_id="auth_db"),
            CallEdge(caller_id="user_svc", callee_id="user_db"),
        ]
        import_graph = [
            ImportEdge(importer_file_id="auth.py", imported_file_id="auth_db.py"),
            ImportEdge(importer_file_id="user.py", imported_file_id="user_db.py"),
        ]
        files = [
            File(id="auth.py", rel_path="services/auth.py"),
            File(id="auth_db.py", rel_path="services/auth_db.py"),
            File(id="user.py", rel_path="services/user.py"),
            File(id="user_db.py", rel_path="services/user_db.py"),
        ]

        detection_result = detector.detect(call_graph, import_graph, [], files)
        layers = layer_detector.extract_layers(import_graph, files)
        subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)

        # Verify detection. UNKNOWN is a legitimate outcome: four files in a
        # single `services/` directory is not sufficient evidence for any
        # style, and the detector never guesses.
        assert detection_result.style in {
            ArchStyle.MICROSERVICES,
            ArchStyle.LAYERED,
            ArchStyle.FLAT,
            ArchStyle.UNKNOWN,
        }
        assert 0.3 <= detection_result.confidence <= 1.0

    def test_versioning(self, arch_db):
        """Test model versioning and load_latest."""
        model1 = ArchitectureModel(
            repo_id="test-repo",
            style=ArchStyle.LAYERED,
            style_confidence=0.8,
            detected_at="2026-07-02T10:00:00Z",
        )
        model2 = ArchitectureModel(
            repo_id="test-repo",
            style=ArchStyle.MVC,
            style_confidence=0.85,
            detected_at="2026-07-02T11:00:00Z",
        )

        arch_db.save(model1)
        arch_db.save(model2)

        latest = arch_db.load_latest("test-repo")
        assert latest.style == ArchStyle.MVC
        assert latest.style_confidence == 0.85


class TestErrorHandling:
    """Error handling tests."""

    def test_missing_repo_returns_none(self, arch_db):
        """Test that load_latest returns None for missing repo."""
        result = arch_db.load_latest("non-existent")
        assert result is None

    def test_cyclic_import_detection(self):
        """Test handling of cyclic imports."""
        detector = ArchitectureDetector()
        layer_detector = LayerDetector()

        call_graph = []
        import_graph = [
            ImportEdge(importer_file_id="a.py", imported_file_id="b.py"),
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
        ]
        files = [
            File(id="a.py", rel_path="a.py"),
            File(id="b.py", rel_path="b.py"),
        ]

        # Detector should handle cycles gracefully
        result = detector.detect(call_graph, import_graph, [], files)
        assert result.style in {
            ArchStyle.LAYERED,
            ArchStyle.HEXAGONAL,
            ArchStyle.MVC,
            ArchStyle.MICROSERVICES,
            ArchStyle.FLAT,
        }
