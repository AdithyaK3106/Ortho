# task-005: Performance Targets
## Measurable Acceptance Criteria (ARCHITECT)

**Date:** 2026-06-30  
**Purpose:** Define reproducible performance goals for architecture detection  
**Scope:** Detection time, memory, hardware assumptions

---

## Repository Size Categories

### Small Repository (Target for Phase 1 validation)
- **File count:** 20–100 files
- **Node count (import graph):** 20–100 nodes
- **Edge count (import graph):** 30–200 edges
- **Symbol count:** 100–500 symbols
- **Call edges:** 100–500 edges
- **Example:** Small Flask app, utility library

### Medium Repository (Realistic production use case)
- **File count:** 100–500 files
- **Node count (import graph):** 100–500 nodes
- **Edge count (import graph):** 200–2000 edges
- **Symbol count:** 500–5000 symbols
- **Call edges:** 500–5000 edges
- **Example:** Medium Django project, microservice framework

### Large Repository (Stress test)
- **File count:** 500–2000 files
- **Node count (import graph):** 500–2000 nodes
- **Edge count (import graph):** 2000–10000 edges
- **Symbol count:** 5000–50000 symbols
- **Call edges:** 5000–50000 edges
- **Example:** Large monolithic application, multi-service codebase

---

## Hardware Assumptions

**Development machine (baseline):**
- **CPU:** 4-core 2.5 GHz (2019-era Intel i5 or equivalent)
- **RAM:** 8 GB
- **Disk:** SSD (local files)
- **Python version:** 3.10+
- **Environment:** No competing processes

**Performance measured on this baseline.**

---

## Execution Profile

### Cold Execution (First run)
- Database is empty or outdated
- All graphs built from scratch
- No caching
- Full metrics computation

### Warm Execution (Incremental re-detection)
- Database contains previous results
- Graphs loaded from cache (if implemented)
- Incremental metrics (Phase 2+)

**Phase 1 acceptance criteria focus on cold execution.**

---

## Measurable Acceptance Criteria

### ArchitectureDetector.detect()

| Category | Small Repo | Medium Repo | Large Repo | Target |
|----------|-----------|-----------|-----------|---------|
| **Cold execution time** | < 100ms | < 500ms | < 2s | Baseline |
| **Metrics computation** | < 50ms | < 200ms | < 1s | Baseline |
| **Score calculation** | < 10ms | < 50ms | < 200ms | Baseline |
| **Peak memory** | < 50 MB | < 200 MB | < 500 MB | Baseline |

**Pass criteria:** All measurements ≤ baseline on development machine.

**Rationale:** Keeping detection sub-second for medium repos ensures responsive CLI UX.

---

### LayerDetector.detect_layers()

| Category | Small Repo | Medium Repo | Large Repo | Target |
|----------|-----------|-----------|-----------|---------|
| **Topological sort** | < 10ms | < 50ms | < 200ms | Baseline |
| **Layer clustering** | < 5ms | < 20ms | < 100ms | Baseline |
| **Semantic naming** | < 5ms | < 30ms | < 150ms | Baseline |
| **Violation detection** | < 10ms | < 100ms | < 500ms | Baseline |

**Pass criteria:** Total layer detection ≤ 30ms (small), 150ms (medium), 1s (large).

---

### SubsystemDetector.detect_subsystems()

| Category | Small Repo | Medium Repo | Large Repo | Target |
|----------|-----------|-----------|-----------|---------|
| **Community detection (Louvain)** | < 20ms | < 200ms | < 1s | Baseline |
| **Coupling calculation** | < 10ms | < 50ms | < 200ms | Baseline |
| **Naming inference** | < 5ms | < 20ms | < 100ms | Baseline |

**Pass criteria:** Total subsystem detection ≤ 50ms (small), 300ms (medium), 1.5s (large).

---

### End-to-End ArchitectureModel Detection

| Category | Small Repo | Medium Repo | Large Repo | Target |
|----------|-----------|-----------|-----------|---------|
| **Full detect() → result** | < 200ms | < 750ms | < 3.5s | Combined |
| **Peak memory** | < 50 MB | < 200 MB | < 500 MB | Combined |
| **Memory peak (after result)** | < 10 MB | < 50 MB | < 100 MB | Retained |

**Pass criteria:** Full detection within targets on development machine (cold execution).

---

## Memory Profile

### Expected Memory Usage (Cold Execution)

| Phase | Small | Medium | Large | Rationale |
|-------|-------|--------|-------|-----------|
| Graph loading | 5 MB | 20 MB | 100 MB | File + symbol nodes/edges |
| Metrics cache | 1 MB | 5 MB | 20 MB | Cached scores |
| Louvain intermediate | 5 MB | 50 MB | 200 MB | Community detection temp |
| **Peak total** | 15 MB | 100 MB | 350 MB | — |
| **Retained (result)** | 2 MB | 10 MB | 30 MB | ArchitectureModel only |

**Pass criteria:** Peak memory ≤ targets. Retained memory (after detection) < 10% of peak.

---

## Warm Execution (Incremental, Phase 2+)

### Expected Improvement (not Phase 1 requirement)

If caching is implemented:
- Cold: 750ms (medium repo)
- Warm: 100ms (medium repo) — 7.5x faster
- Incremental (1 file changed): 50ms (medium repo)

**Phase 1 baseline:** Cold execution only.

---

## Test Harness

### Measurement Protocol

```python
# Pseudocode for test
import time
import psutil

def measure_detection(repo_path):
    # Warm up (not measured)
    db = OrthoDatabase(repo_path)
    db.migrate()
    
    # Measure cold execution
    process = psutil.Process()
    
    # Get baseline memory
    mem_before = process.memory_info().rss
    
    # Time the detection
    detector = ArchitectureDetector(db, repo_id)
    start = time.perf_counter()
    result = detector.detect()
    elapsed = time.perf_counter() - start
    
    # Get peak memory
    mem_after = process.memory_info().rss
    mem_peak_used = mem_after - mem_before
    
    return {
        'elapsed_ms': elapsed * 1000,
        'peak_memory_mb': mem_peak_used / (1024 * 1024),
        'result': result,
    }
```

### Test Execution

1. **Small repo fixture:** Run 5 times, report median elapsed time
2. **Medium repo fixture:** Run 3 times, report median elapsed time
3. **Large repo fixture:** Run 1 time (setup cost), report elapsed time
4. **Memory:** Peak RSS across all runs

---

## Acceptance Criteria Summary

| Criterion | Small | Medium | Large | Status |
|-----------|-------|--------|-------|--------|
| detect() completes | ✅ | ✅ | ✅ | Must pass |
| detect() time ≤ target | ✅ | ✅ | ✅ | Must pass |
| Peak memory ≤ target | ✅ | ✅ | ✅ | Must pass |
| Result is valid | ✅ | ✅ | ✅ | Must pass |
| Deterministic (2 runs same) | ✅ | ✅ | ✅ | Must pass |

---

## Degradation Scenarios (Not Optimization Targets)

If performance exceeds targets:

| Scenario | Action | Phase |
|----------|--------|-------|
| Small repo > 200ms | Investigate; document; accept if < 500ms | 1 |
| Medium repo > 1s | Document; add caching ADR | 2 |
| Large repo > 5s | Document; defer large-repo support to Phase 2 | 1 |
| Memory > 600 MB | Document; note limitation | 1 |

**Principle:** Phase 1 establishes baseline. Optimization deferred to Phase 2 if needed.

---

## How to Measure (TEST-DESIGNER Guidance)

### Test fixture setup
1. Create small-repo/ (20 files, 50 edges)
2. Create medium-repo/ (200 files, 500 edges)
3. Create large-repo/ (1000 files, 3000 edges)

### Run measurement
```bash
# TEST-DESIGNER runs this in test harness
python -m pytest tests/test_performance.py -v --benchmark-only
```

### Expected output
```
test_detect_small ... PASSED (85 ms)
test_detect_medium ... PASSED (420 ms)
test_detect_large ... PASSED (1800 ms)
test_memory_small ... PASSED (peak 42 MB)
test_memory_medium ... PASSED (180 MB)
test_memory_large ... PASSED (420 MB)
```

---

**Prepared by:** ARCHITECT  
**Status:** Refinement — Performance targets established, not optimized
