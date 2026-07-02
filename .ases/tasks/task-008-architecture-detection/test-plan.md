# task-008: Architecture Detection — Test Plan

**Task ID:** task-008  
**Workflow:** `.ases/workflows/feature.md` (GATE 4: Test Coverage Review)  
**TEST-DESIGNER:** Test Suite Design Session  
**Date:** 2026-07-02

---

## Test Strategy Overview

**Approach:** TDD with shadow testing (write tests concurrent with implementation)

**Test Categories:**
1. **Unit Tests** (40+) — Individual components in isolation
2. **Integration Tests** (15+) — Component interactions
3. **Edge Cases** (10+) — Boundary values, error conditions
4. **Property-Based Tests** (hypothesis, ≥10 generated cases)
5. **Real-Repository Tests** (fastapi, django baselines)

**Expected Total:** 65+ tests, ≥85% coverage

---

## Unit Tests (40+)

### ArchitectureDetector Tests (15+)

**Happy Path:**
- `test_detect_layered_pattern` — Known 3-layer structure returns layered with confidence 0.8+
- `test_detect_hexagonal_pattern` — Core + 2 adapters returns hexagonal with confidence 0.65+
- `test_detect_mvc_pattern` — Model/View/Controller separation returns mvc with confidence 0.7+
- `test_detect_microservices_pattern` — 4+ subsystems returns microservices with confidence 0.6+
- `test_detect_flat_pattern` — No structure returns flat with confidence 0.3–0.8

**Confidence Scoring:**
- `test_confidence_range` — All detector scores in [0.0, 1.0]
- `test_confidence_deterministic` — Same input always produces same score
- `test_tie_breaking_order` — Tied scores resolved by priority order (layered > mvc > hexagonal > microservices > flat)

**Evidence Generation:**
- `test_evidence_list_not_empty` — Evidence list always populated
- `test_evidence_includes_style` — Evidence mentions detected style
- `test_evidence_includes_confidence` — Evidence shows confidence score

**Edge Cases:**
- `test_empty_graphs` — Empty call/import graphs handled gracefully
- `test_single_file_repo` — Single file returns valid architecture
- `test_all_external_imports` — No internal dependencies returns flat
- `test_null_values` — Null inputs handled without crash

### LayerDetector Tests (10+)

**Happy Path:**
- `test_extract_3_layers` — DAG with 3 levels extracts 3 layers correctly
- `test_layer_numbering` — Layer 0=data, Layer 1=business, Layer 2=presentation
- `test_semantic_naming` — "repository" files → Layer 0, "service" → Layer 1, "controller" → Layer 2

**Topological Sort:**
- `test_topological_order` — Returned layers in correct order (Layer 0 first)
- `test_acyclic_validation` — Acyclic DAG passes; cyclic graph rejected with evidence

**Edge Cases:**
- `test_single_layer` — Single file in isolation
- `test_no_imports` — Disconnected modules each form separate layer
- `test_semantic_naming_partial` — Some files match naming, others inferred
- `test_layer_dependency_chain` — Layer dependencies only downward

### SubsystemDetector Tests (10+)

**Clustering:**
- `test_louvain_clustering` — Call graph clusters into subsystems
- `test_subsystem_naming` — Subsystems named from file path prefixes
- `test_subsystem_stability` — Same input produces same clustering (seed=42)

**Coupling Score:**
- `test_coupling_score_range` — Coupling always in [0.0, 1.0]
- `test_tight_coupling` — Intra-module calls > inter-module → low coupling score
- `test_loose_coupling` — Many inter-module calls → high coupling score

**Edge Cases:**
- `test_single_subsystem` — All modules in one community
- `test_many_subsystems` — Highly fragmented graph (each module isolated)
- `test_empty_call_graph` — No calls, no subsystems
- `test_partial_connectivity` — Some modules isolated from call graph

### ArchitectureModelStore Tests (5+)

**CRUD:**
- `test_save_and_load` — Save model, load it back, verify equality
- `test_versioning` — Multiple saves create timestamped versions
- `test_load_latest` — load_latest returns most recent by detected_at

**Edge Cases:**
- `test_duplicate_save` — Save same model twice (idempotent)
- `test_missing_repo` — load_latest on non-existent repo returns None

---

## Integration Tests (15+)

### End-to-End Pipeline:

**test_full_pipeline_simple_repo** (5+ tests)
- Load synthetic repo (3-layer structure)
- Run full detection (detector → layers → subsystems → store)
- Verify: ArchitectureModel has correct style, confidence, layers, subsystems
- Verify: Model saved to SQLite and retrievable

**test_full_pipeline_complex_repo** (5+ tests)
- Load synthetic microservices-like repo (4+ subsystems, varied coupling)
- Run detection
- Verify: Microservices detected with appropriate confidence
- Verify: Subsystems match expected clustering

**test_full_pipeline_with_cycles** (5+ tests)
- Load repo with cyclic imports
- Run detection
- Verify: Layered pattern rejected (not acyclic)
- Verify: Alternative patterns scored lower
- Verify: Evidence includes cycle detection

---

## Property-Based Tests (hypothesis, ≥10 generated cases)

**test_detector_confidence_bounds** (property-based)
- Generate random call/import graphs
- Run detector on each
- Assert: confidence always in [0.0, 1.0]
- Assert: style is one of the 5 valid types

**test_layer_extraction_deterministic** (property-based)
- Generate DAGs of varying sizes (5–50 nodes)
- Extract layers twice on same graph
- Assert: identical results both times

**test_subsystem_stability** (property-based)
- Generate call graphs with varying sizes (10–100 symbols)
- Run Louvain twice
- Assert: identical clustering both times (seed=42)

---

## Real-Repository Tests

### Baseline Repos (Located in `.../Repos/`)

**test_fastapi_detection**
- Load real fastapi repo
- Run detection
- Assert: confidence in expected range (0.4–1.0)
- Assert: style is one of the 5 patterns
- Assert: no crashes or exceptions
- Benchmark: fastapi = microservices-like (informational)

**test_django_detection**
- Load real django repo
- Run detection
- Assert: style is likely mvc or layered (no assertion, informational)
- Assert: confidence >= 0.3 (weak pattern is still valid)

**test_real_repo_layers**
- Extract layers from real repo
- Assert: layers non-empty
- Assert: all file_ids valid
- Assert: layer numbering correct

**test_real_repo_subsystems**
- Detect subsystems from real repo
- Assert: subsystems non-empty
- Assert: coupling scores in [0.0, 1.0]

---

## Sample Test Code (Working Examples)

### Unit Test: ArchitectureDetector

```python
import pytest
from arch_intelligence.arch_detector import ArchitectureDetector
from arch_intelligence.types import ArchStyle


@pytest.fixture
def detector():
    return ArchitectureDetector()


def test_detect_layered_pattern(detector):
    """Test detection of layered architecture."""
    # Create synthetic layered graph
    call_graph = []
    import_graph = [
        # Layer 0 (data) files
        {"importer_file_id": "a.py", "imported_file_id": None},
        # Layer 1 (business) imports Layer 0
        {"importer_file_id": "b.py", "imported_file_id": "a.py"},
        # Layer 2 (presentation) imports Layer 1
        {"importer_file_id": "c.py", "imported_file_id": "b.py"},
    ]
    files = [
        {"id": "a.py", "rel_path": "data/repository.py"},
        {"id": "b.py", "rel_path": "service/user_service.py"},
        {"id": "c.py", "rel_path": "api/controller.py"},
    ]
    
    result = detector.detect(call_graph, import_graph, [], files)
    
    assert result.style == ArchStyle.LAYERED
    assert result.confidence >= 0.8
    assert len(result.evidence) > 0
```

### Integration Test: Full Pipeline

```python
def test_full_pipeline_simple_repo(detector, layer_detector, subsystem_detector, model_store):
    """Test complete detection pipeline."""
    # Setup synthetic repo with 3 layers
    call_graph = [...]
    import_graph = [...]
    files = [...]
    
    # Run detection
    detection_result = detector.detect(call_graph, import_graph, [], files)
    layers = layer_detector.extract_layers(import_graph, files)
    subsystems = subsystem_detector.detect_subsystems(call_graph, [], files)
    
    # Build model
    model = ArchitectureModel(
        repo_id="test-repo",
        style=detection_result.style,
        style_confidence=detection_result.confidence,
        layers=layers,
        subsystems=subsystems,
        evidence=detection_result.evidence,
    )
    
    # Save and retrieve
    model_id = model_store.save(model)
    loaded = model_store.load_latest("test-repo")
    
    assert loaded.repo_id == "test-repo"
    assert loaded.style == detection_result.style
    assert len(loaded.layers) == 3
```

### Property-Based Test (hypothesis)

```python
from hypothesis import given, strategies as st


@given(
    num_files=st.integers(min_value=1, max_value=100),
    coupling_factor=st.floats(min_value=0.0, max_value=1.0),
)
def test_detector_confidence_bounds(num_files, coupling_factor, detector):
    """Property: confidence always in [0.0, 1.0]."""
    # Generate random graphs
    call_graph = [...]  # Generated based on num_files, coupling_factor
    import_graph = [...]
    files = [...]
    
    result = detector.detect(call_graph, import_graph, [], files)
    
    assert 0.0 <= result.confidence <= 1.0
    assert result.style in [
        ArchStyle.LAYERED,
        ArchStyle.HEXAGONAL,
        ArchStyle.MVC,
        ArchStyle.MICROSERVICES,
        ArchStyle.FLAT,
    ]
```

---

## Test Execution Policy

**Pilot Test (GATE 4):** Run 5-10 sample tests before full approval
- Validates: imports work, test code syntax valid, environment setup correct
- Command: `pytest packages/arch-intelligence/tests/ -k "test_sample" -v`

**Full Suite (GATE 5):** Run all 65+ tests with coverage
- Command: `pytest packages/arch-intelligence/tests/ -v --cov=packages/arch-intelligence`
- Expected: ≥85% coverage, 100% pass rate (or pre-approved xfail)

**Regression (GATE 5):** Full test suite across all packages
- Command: `pytest -v`
- Expected: All existing tests (repo-intelligence, context-hub) still pass

---

## Known Limitations (If Any)

None — all acceptance criteria expected to be fully tested.

---

## Test Metrics Summary

| Category | Count | Status |
|----------|-------|--------|
| Unit tests | 40+ | Ready |
| Integration tests | 15+ | Ready |
| Edge cases | 10+ | Ready |
| Property-based (hypothesis) | ≥10 | Ready |
| Real-repo tests | 4+ | Ready |
| **Total** | **65+** | **Ready** |
| **Expected coverage** | **≥85%** | **Expected** |
| **Expected pass rate** | **100%** | **Expected** |

---

*Test plan prepared by TEST-DESIGNER role.*  
*Ready for human review and approval at GATE 4.*
