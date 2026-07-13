"""Hard and edge-case tests for ArchitectureDetectorV2."""

import pytest
from arch_intelligence.arch_detector_v2 import ArchitectureDetectorV2, CallEdge, ImportEdge, File
from arch_intelligence.types import ArchStyle


@pytest.fixture
def detector():
    return ArchitectureDetectorV2()


class TestBoundaryConditions:
    """Test boundary and edge case conditions."""

    def test_empty_repository(self, detector):
        """Empty repo with no files."""
        result = detector.detect([], [], [], [])
        assert result.style == ArchStyle.UNKNOWN
        assert result.confidence == 0.0

    def test_single_file(self, detector):
        """Single file in repo."""
        files = [File(id="main.py", rel_path="main.py")]
        result = detector.detect([], [], [], files)
        assert result.style == ArchStyle.FLAT
        assert result.confidence >= 0.5

    def test_two_files_no_imports(self, detector):
        """Two independent files (no imports)."""
        files = [
            File(id="a.py", rel_path="a.py"),
            File(id="b.py", rel_path="b.py"),
        ]
        result = detector.detect([], [], [], files)
        assert result.style in (ArchStyle.FLAT, ArchStyle.UNKNOWN)
        assert result.confidence >= 0.0

    def test_thousand_files_flat(self, detector):
        """1000 files in single directory (flat structure)."""
        files = [File(id=f"f{i}.py", rel_path=f"f{i}.py") for i in range(1000)]
        result = detector.detect([], [], [], files)
        assert result.style == ArchStyle.FLAT
        assert 0.0 <= result.confidence <= 1.0

    def test_layered_three_layer_perfect(self, detector):
        """Perfect 3-layer structure (presentation→service→data)."""
        files = [
            File(id="api.py", rel_path="api/routes.py"),
            File(id="service.py", rel_path="services/logic.py"),
            File(id="db.py", rel_path="data/models.py"),
        ]
        imports = [
            ImportEdge(importer_file_id="api.py", imported_file_id="service.py"),
            ImportEdge(importer_file_id="service.py", imported_file_id="db.py"),
        ]
        result = detector.detect([], imports, [], files)
        assert result.style == ArchStyle.LAYERED
        assert result.confidence >= 0.5  # Minimum evidence threshold

    def test_layered_reverse_flow(self, detector):
        """Backward flow: data→service→api (violation)."""
        files = [
            File(id="db.py", rel_path="data/models.py"),
            File(id="service.py", rel_path="services/logic.py"),
            File(id="api.py", rel_path="api/routes.py"),
        ]
        imports = [
            # Wrong direction: data imports service
            ImportEdge(importer_file_id="db.py", imported_file_id="service.py"),
            # Wrong: service imports api
            ImportEdge(importer_file_id="service.py", imported_file_id="api.py"),
        ]
        result = detector.detect([], imports, [], files)
        # Should detect as layered but with lower confidence due to reverse flow
        assert result.style in (ArchStyle.LAYERED, ArchStyle.UNKNOWN)
        assert 0.0 <= result.confidence <= 1.0

    def test_layered_single_layer_only(self, detector):
        """Only one layer band present (e.g., only 'models/')."""
        files = [
            File(id="m1.py", rel_path="models/user.py"),
            File(id="m2.py", rel_path="models/post.py"),
        ]
        result = detector.detect([], [], [], files)
        # Single layer = ambiguous, likely FLAT or UNKNOWN
        assert result.style in (ArchStyle.FLAT, ArchStyle.UNKNOWN)

    def test_microservices_three_services_isolated(self, detector):
        """Microservices with 3 isolated services (may be detected or flat depending on structure)."""
        files = [
            # Auth service
            File(id="auth_main.py", rel_path="auth_service/__main__.py"),
            File(id="auth.py", rel_path="auth_service/service.py"),
            # User service
            File(id="user_main.py", rel_path="user_service/__main__.py"),
            File(id="user.py", rel_path="user_service/service.py"),
            # Order service
            File(id="order_main.py", rel_path="order_service/__main__.py"),
            File(id="order.py", rel_path="order_service/service.py"),
        ]
        calls = [
            CallEdge(caller_id="auth_main", callee_id="auth"),
            CallEdge(caller_id="user_main", callee_id="user"),
            CallEdge(caller_id="order_main", callee_id="order"),
        ]
        imports = [
            ImportEdge(importer_file_id="auth_main.py", imported_file_id="auth.py"),
            ImportEdge(importer_file_id="user_main.py", imported_file_id="user.py"),
            ImportEdge(importer_file_id="order_main.py", imported_file_id="order.py"),
        ]
        result = detector.detect(calls, imports, [], files)
        # 3+ components with entry points may detect as microservices OR flat (both valid)
        assert result.style in (ArchStyle.MICROSERVICES, ArchStyle.FLAT)
        assert 0.5 <= result.confidence <= 1.0

    def test_microservices_no_entry_points(self, detector):
        """Microservices without entry points (library-style)."""
        files = [
            File(id="auth.py", rel_path="auth_service/handler.py"),
            File(id="user.py", rel_path="user_service/handler.py"),
            File(id="order.py", rel_path="order_service/handler.py"),
        ]
        result = detector.detect([], [], [], files)
        # 3 components but no entry points = may not detect as microservices
        assert result.style in (ArchStyle.MICROSERVICES, ArchStyle.FLAT, ArchStyle.UNKNOWN)

    def test_microservices_with_cross_imports(self, detector):
        """Microservices with some cross-service imports (coupling)."""
        files = [
            File(id="auth_main.py", rel_path="auth_service/__main__.py"),
            File(id="auth.py", rel_path="auth_service/service.py"),
            File(id="user_main.py", rel_path="user_service/__main__.py"),
            File(id="user.py", rel_path="user_service/service.py"),
            File(id="order_main.py", rel_path="order_service/__main__.py"),
            File(id="order.py", rel_path="order_service/service.py"),
        ]
        calls = [
            CallEdge(caller_id="auth_main", callee_id="auth"),
            CallEdge(caller_id="user_main", callee_id="user"),
            CallEdge(caller_id="order_main", callee_id="order"),
        ]
        imports = [
            # Internal service imports
            ImportEdge(importer_file_id="auth_main.py", imported_file_id="auth.py"),
            ImportEdge(importer_file_id="user_main.py", imported_file_id="user.py"),
            ImportEdge(importer_file_id="order_main.py", imported_file_id="order.py"),
            # Cross-service import (coupling)
            ImportEdge(importer_file_id="auth.py", imported_file_id="user.py"),
            ImportEdge(importer_file_id="order.py", imported_file_id="auth.py"),
        ]
        result = detector.detect(calls, imports, [], files)
        # Should still detect as microservices despite coupling, or may degrade
        assert result.style in (ArchStyle.MICROSERVICES, ArchStyle.LAYERED, ArchStyle.FLAT)

    def test_mvc_pattern(self, detector):
        """MVC pattern detection."""
        files = [
            File(id="user_view.py", rel_path="views/user.py"),
            File(id="user_controller.py", rel_path="controllers/user.py"),
            File(id="user_model.py", rel_path="models/user.py"),
        ]
        imports = [
            ImportEdge(importer_file_id="user_view.py", imported_file_id="user_controller.py"),
            ImportEdge(importer_file_id="user_controller.py", imported_file_id="user_model.py"),
        ]
        result = detector.detect([], imports, [], files)
        # Should detect structure (may not be strict MVC but should not be UNKNOWN)
        assert result.style in (ArchStyle.MVC, ArchStyle.LAYERED)

    def test_circular_imports(self, detector):
        """Circular imports between modules."""
        files = [
            File(id="a.py", rel_path="a.py"),
            File(id="b.py", rel_path="b.py"),
        ]
        imports = [
            ImportEdge(importer_file_id="a.py", imported_file_id="b.py"),
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
        ]
        result = detector.detect([], imports, [], files)
        # Circular imports = architectural issue, but detector should handle gracefully
        assert result.style in (ArchStyle.FLAT, ArchStyle.UNKNOWN)
        assert 0.0 <= result.confidence <= 1.0

    def test_deep_nesting_100_levels(self, detector):
        """Very deep directory nesting (100+ levels)."""
        # Create 100-level deep path
        path = "/".join([f"dir{i}" for i in range(100)]) + "/main.py"
        files = [File(id="deep.py", rel_path=path)]
        result = detector.detect([], [], [], files)
        # Should not crash, should handle gracefully
        assert result.style in (ArchStyle.FLAT, ArchStyle.UNKNOWN)
        assert 0.0 <= result.confidence <= 1.0

    def test_special_chars_in_path(self, detector):
        """Paths with special characters."""
        files = [
            File(id="f1.py", rel_path="service$name/handler.py"),
            File(id="f2.py", rel_path="data@model/db.py"),
        ]
        result = detector.detect([], [], [], files)
        # Should handle without crashing
        assert result.style in (ArchStyle.FLAT, ArchStyle.LAYERED, ArchStyle.UNKNOWN)

    def test_unicode_in_path(self, detector):
        """Unicode characters in paths."""
        files = [
            File(id="f1.py", rel_path="café/service.py"),
            File(id="f2.py", rel_path="日本語/db.py"),
        ]
        result = detector.detect([], [], [], files)
        # Should handle unicode gracefully
        assert result.style in (ArchStyle.FLAT, ArchStyle.UNKNOWN)

    def test_many_external_imports(self, detector):
        """Many external (third-party) imports."""
        files = [File(id="main.py", rel_path="main.py")]
        # Simulate external imports (no imported_file_id)
        imports = [
            ImportEdge(importer_file_id="main.py", imported_module="flask"),
            ImportEdge(importer_file_id="main.py", imported_module="django"),
            ImportEdge(importer_file_id="main.py", imported_module="celery"),
        ]
        result = detector.detect([], imports, [], files)
        # External imports should not affect structure detection
        assert result.style == ArchStyle.FLAT

    def test_all_layer_bands_present(self, detector):
        """All three layer bands have files."""
        files = [
            File(id="f1.py", rel_path="api/routes.py"),      # presentation
            File(id="f2.py", rel_path="services/logic.py"),  # business
            File(id="f3.py", rel_path="data/models.py"),     # data
            File(id="f4.py", rel_path="views/ui.py"),        # presentation
            File(id="f5.py", rel_path="domain/core.py"),     # business
            File(id="f6.py", rel_path="db/schema.py"),       # data
        ]
        result = detector.detect([], [], [], files)
        # All 3 layers present = likely LAYERED
        assert result.style in (ArchStyle.LAYERED, ArchStyle.UNKNOWN)

    def test_confidence_bounds(self, detector):
        """Confidence always in [0.0, 1.0]."""
        # Various configurations
        configs = [
            ([], [], [], []),  # empty
            ([], [], [], [File(id="f.py", rel_path="f.py")]),  # single file
            ([], [], [], [File(id=f"f{i}.py", rel_path=f"f{i}.py") for i in range(100)]),  # many files
        ]
        for calls, imports, symbols, files in configs:
            result = detector.detect(calls, imports, symbols, files)
            assert 0.0 <= result.confidence <= 1.0, \
                f"Confidence out of bounds: {result.confidence}"

    def test_detector_never_crashes(self, detector):
        """Detector handles all inputs without crashing."""
        # Pathological cases
        test_cases = [
            # Null/empty cases
            ([], [], [], []),
            # Circular references
            ([CallEdge(caller_id="a", callee_id="a")], [], [], [File(id="a.py", rel_path="a.py")]),
            # Many files
            ([], [], [], [File(id=f"f{i}.py", rel_path=f"f{i}.py") for i in range(10000)]),
            # Orphaned imports (file doesn't exist)
            ([], [ImportEdge(importer_file_id="missing.py", imported_file_id="also_missing.py")], [], []),
        ]
        for calls, imports, symbols, files in test_cases:
            result = detector.detect(calls, imports, symbols, files)
            # Should return valid result, not crash
            assert result is not None
            assert result.style in (
                ArchStyle.UNKNOWN, ArchStyle.FLAT, ArchStyle.LAYERED,
                ArchStyle.MICROSERVICES, ArchStyle.MVC, ArchStyle.HEXAGONAL
            )
            assert 0.0 <= result.confidence <= 1.0
