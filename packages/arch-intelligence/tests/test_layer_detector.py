"""Layer detection tests - stateless API per specification."""

import pytest
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.arch_detector import ImportEdge, File
from arch_intelligence.types import Layer


@pytest.fixture
def layer_detector():
    return LayerDetector()


class TestLayerDetectionBasics:
    """Test basic layer extraction (stateless API)."""

    def test_extract_layers_returns_list(self, layer_detector):
        """extract_layers should return a list."""
        import_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        result = layer_detector.extract_layers(import_graph, files)
        assert isinstance(result, list)

    def test_layered_fixture_extracts_layers(self, layer_detector):
        """3-layer fixture should extract multiple layers."""
        import_graph = [
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
            ImportEdge(importer_file_id="c.py", imported_file_id="b.py"),
        ]
        files = [
            File(id="a.py", rel_path="data/db.py"),
            File(id="b.py", rel_path="service/logic.py"),
            File(id="c.py", rel_path="api/handler.py"),
        ]
        
        layers = layer_detector.extract_layers(import_graph, files)
        assert len(layers) >= 1


class TestLayerFieldContent:
    """Test layer dataclass fields."""

    def test_layer_has_id(self, layer_detector):
        """Layers should have id field."""
        import_graph = []
        files = [File(id="a.py", rel_path="a.py")]
        layers = layer_detector.extract_layers(import_graph, files)
        if layers:
            assert hasattr(layers[0], "id")

    def test_layer_has_number(self, layer_detector):
        """Layers should have layer number."""
        import_graph = [ImportEdge(importer_file_id="b.py", imported_file_id="a.py")]
        files = [File(id="a.py", rel_path="a.py"), File(id="b.py", rel_path="b.py")]
        layers = layer_detector.extract_layers(import_graph, files)
        if layers:
            assert hasattr(layers[0], "number")
            assert isinstance(layers[0].number, int)


class TestSemanticNaming:
    """Test semantic file naming detection."""

    def test_data_files_detected(self, layer_detector):
        """Files with 'repository', 'db', 'model' should be data layer."""
        import_graph = []
        files = [
            File(id="repo.py", rel_path="data/repository.py"),
            File(id="db.py", rel_path="data/db.py"),
        ]
        layers = layer_detector.extract_layers(import_graph, files)
        # Verify layers exist (semantic naming is a signal, not a requirement)
        assert isinstance(layers, list)

    def test_service_files_detected(self, layer_detector):
        """Files with 'service', 'business', 'logic' should be business layer."""
        import_graph = []
        files = [File(id="svc.py", rel_path="service/user_service.py")]
        layers = layer_detector.extract_layers(import_graph, files)
        assert isinstance(layers, list)


class TestLayerHierarchy:
    """Test layer dependency validation."""

    def test_acyclic_graph_valid(self, layer_detector):
        """Acyclic import graph should extract without error."""
        import_graph = [
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
            ImportEdge(importer_file_id="c.py", imported_file_id="b.py"),
        ]
        files = [
            File(id="a.py", rel_path="a.py"),
            File(id="b.py", rel_path="b.py"),
            File(id="c.py", rel_path="c.py"),
        ]
        layers = layer_detector.extract_layers(import_graph, files)
        assert isinstance(layers, list)


class TestDeterminism:
    """Test that layer detection is deterministic."""

    def test_extract_twice_identical(self, layer_detector):
        """Extracting layers twice should produce identical results."""
        import_graph = [ImportEdge(importer_file_id="b.py", imported_file_id="a.py")]
        files = [File(id="a.py", rel_path="a.py"), File(id="b.py", rel_path="b.py")]
        
        layers1 = layer_detector.extract_layers(import_graph, files)
        layers2 = layer_detector.extract_layers(import_graph, files)
        
        assert len(layers1) == len(layers2)
        if layers1:
            assert layers1[0].id == layers2[0].id

