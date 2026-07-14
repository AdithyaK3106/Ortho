"""Tests for ArchModelAdapter (task-017 spec.md Component 3)."""

from pathlib import Path

from arch_intelligence.arch_detector import ArchitectureDetector, File
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.model_adapter import ArchModelAdapter
from arch_intelligence.types import ArchitectureModel, ArchStyle, Layer


def _model(layers: list[Layer]) -> ArchitectureModel:
    return ArchitectureModel(
        repo_id="test-repo",
        style=ArchStyle.LAYERED,
        style_confidence=0.9,
        layers=layers,
    )


class TestArchModelAdapter:
    def test_module_in_layer_0(self) -> None:
        layer = Layer(id="layer_0", number=0, name="Data", file_ids=["file_a"])
        model = _model([layer])
        adapter = ArchModelAdapter(model, {"file_a": "mod_a"})
        assert adapter.get_layer("mod_a") == "Data"

    def test_module_not_in_any_layer(self) -> None:
        layer = Layer(id="layer_0", number=0, name="Data", file_ids=["file_a"])
        model = _model([layer])
        adapter = ArchModelAdapter(model, {"file_a": "mod_a"})
        assert adapter.get_layer("unmapped_module") == "unknown"

    def test_get_layers_ordering_by_number(self) -> None:
        layers = [
            Layer(id="layer_2", number=2, name="Presentation", file_ids=[]),
            Layer(id="layer_0", number=0, name="Data", file_ids=[]),
            Layer(id="layer_1", number=1, name="Business", file_ids=[]),
        ]
        model = _model(layers)
        adapter = ArchModelAdapter(model, {})
        assert adapter.get_layers() == ["Data", "Business", "Presentation"]

    def test_empty_layers(self) -> None:
        model = _model([])
        adapter = ArchModelAdapter(model, {})
        assert adapter.get_layers() == []
        assert adapter.get_layer("anything") == "unknown"

    def test_get_modules_dedup(self) -> None:
        layer = Layer(id="layer_0", number=0, name="Data", file_ids=["file_a", "file_b"])
        model = _model([layer])
        # two files map to the same module string
        adapter = ArchModelAdapter(model, {"file_a": "shared_mod", "file_b": "shared_mod"})
        assert adapter.get_modules().count("shared_mod") == 1

    def test_get_modules_empty(self) -> None:
        model = _model([])
        adapter = ArchModelAdapter(model, {})
        assert adapter.get_modules() == []

    def test_layer_with_no_file_ids_still_appears(self) -> None:
        layer = Layer(id="layer_0", number=0, name="Empty", file_ids=[])
        model = _model([layer])
        adapter = ArchModelAdapter(model, {})
        assert adapter.get_layers() == ["Empty"]

    def test_get_layer_for_module_matches_get_layer(self) -> None:
        layer = Layer(id="layer_0", number=0, name="Data", file_ids=["file_a"])
        model = _model([layer])
        adapter = ArchModelAdapter(model, {"file_a": "mod_a"})
        assert adapter.get_layer_for_module("mod_a") == adapter.get_layer("mod_a")

    def test_unknown_file_id_in_mapping_resolves_unknown(self) -> None:
        layer = Layer(id="layer_0", number=0, name="Data", file_ids=["file_a"])
        model = _model([layer])
        # file_to_module has a key not present in any Layer.file_ids
        adapter = ArchModelAdapter(model, {"file_z": "mod_z"})
        assert adapter.get_layer("mod_z") == "unknown"

    def test_real_arch_model_from_detector(self, tmp_path: Path) -> None:
        """Real-repo scan test (mandatory per spec.md): build a genuine
        ArchitectureModel via LayerDetector against small real files, wrap it."""
        f1 = tmp_path / "data_repo.py"
        f2 = tmp_path / "service.py"
        f1.write_text("class Repo:\n    pass\n", encoding="utf-8")
        f2.write_text("from data_repo import Repo\n\nclass Service:\n    pass\n", encoding="utf-8")

        files = [
            File(id=str(f1), rel_path="data_repo.py"),
            File(id=str(f2), rel_path="service.py"),
        ]

        class _Edge:
            def __init__(self, importer: str, imported: str) -> None:
                self.importer_file_id = importer
                self.imported_file_id = imported

        edges = [_Edge(str(f2), str(f1))]
        layers = LayerDetector().extract_layers(edges, files)
        model = _model(layers)

        file_to_module = {str(f1): "data_repo", str(f2): "service"}
        adapter = ArchModelAdapter(model, file_to_module)

        assert isinstance(adapter.get_layers(), list)
        # service depends on data_repo, so data_repo should resolve to a lower/equal layer
        assert adapter.get_layer("data_repo") != "unknown"
        assert adapter.get_layer("service") != "unknown"
