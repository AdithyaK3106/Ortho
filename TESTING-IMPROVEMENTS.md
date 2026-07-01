# Testing Improvements: ASES Workflow Updates

**Date:** 2026-07-01  
**Motivation:** Task-006 proved that *designed* tests often miss bugs that *real* tests catch. Implementing 3 improvements to prevent regression.

---

## Problem Identified

**Tests designed abstractly catch ~70% of real bugs.** When BUILDER implements code, VERIFIER runs tests, real edge cases emerge:
- Hexagonal pattern misclassification (task-005)
- Import alias handling edge cases (task-006)
- Circular dependency deadlocks (discovered late)

**Root cause:** Tests are written in isolation (TEST-DESIGNER) without shadowing implementation. Property-based testing and real-codebase scanning catch what mocks miss.

---

## Solution: 3 Changes to Feature Workflow

### Change 1: TEST-DESIGNER Shadows BUILDER (Concurrent, Not Sequential)

**Before:**
```
BUILDER → implements code → TEST-DESIGNER → writes tests in isolation
```

**After:**
```
BUILDER ↔ TEST-DESIGNER (concurrent)
  BUILDER writes function → TEST-DESIGNER writes test immediately
  Test fails → BUILDER fixes code → Test passes
  (TDD-style feedback loop)
```

**Impact:**
- Catch assumption mismatches in real time
- Tests drive implementation, not verify it after
- Fewer re-runs (test+code iterate together)

**Workflow Change:**
- Spec (GATE 1) now includes: "TEST-DESIGNER will shadow BUILDER, writing tests as code lands"
- BUILDER and TEST-DESIGNER coordinate (can be same person or parallel roles)

---

### Change 2: Property-Based Tests + hypothesis (GATE 4 Requirement)

**Before:**
```
Unit tests cover happy path and edge cases (manually designed)
```

**After:**
```
Unit tests + property-based tests using hypothesis
  - hypothesis generates 10+ test cases automatically
  - Property: "call graph has no cycles" (verified on all 10+ generated inputs)
  - Tests invariants, not individual cases
```

**Example Property Test:**
```python
from hypothesis import given, strategies as st

@given(st.lists(st.text()))
def test_call_graph_acyclic_property(file_names: list[str]):
    """Property: call graph is always acyclic (no circular calls)"""
    indexer = IncrementalIndexer()
    for name in file_names:
        indexer.add_file(name)
    
    # Invariant: No cycles in call graph
    assert not has_cycle(indexer.call_graph)
```

**Impact:**
- Catches edge cases humans don't think of
- Automatically tests boundary conditions
- Each property test = 10+ unit tests' worth of coverage

**Workflow Change:**
- GATE 4 (Test Coverage Review) now requires:
  - ≥1 property-based test (hypothesis with ≥10 generated cases)
  - Test-plan.md includes evidence of property tests

---

### Change 3: Real-Repo Scan Tests (GATE 4 + GATE 5 Requirement)

**Before:**
```
Tests use mocks or synthetic data
  test_extract_symbols_from_simple_file.py  ← 5 lines of mock Python
```

**After:**
```
Tests scan actual codebase (fastapi from .../Repos/)
  test_scan_fastapi_real_repo()  ← Scans 500+ real files, verifies ≥500 symbols found
```

**Example Real-Repo Test:**
```python
def test_scan_fastapi_real_repo():
    """Real-repo test: Can tool handle real fastapi codebase?"""
    repo_path = Path("C:/Users/urbra/OneDrive/Desktop/Projects/ortho/Repos/fastapi")
    indexer = IncrementalIndexer()
    result = indexer.index_changes(repo_path)
    
    # Assertions on REAL EXTRACTED DATA
    assert result.symbols_count >= 500  # Not mock, real fastapi symbols
    assert result.call_edges >= 200     # Real call graph
    assert result.import_edges >= 50    # Real imports
```

**Available Real Repos:**
- `django` — large, complex
- `fastapi` — medium, well-structured (recommended)
- `langchain` — large, modern Python
- `opentelemetry-demo` — medium
- `supabase-master` — mixed languages

**Impact:**
- Catches bugs that mocks never see (dynamic imports, circular dependencies, etc.)
- Real-world confidence before shipping
- Faster bug discovery (failures in real code are loud and clear)

**Workflow Change:**
- GATE 4 now requires: ≥1 real-repo scan test (using codebase from .../Repos/)
- GATE 5 (VERIFIER) verifies real-repo test actually executed (not mocked)

---

## Changes to ASES Workflow (`.ases/workflows/feature.md`)

### GATE 4: Test Coverage Review

**NEW Requirements:**
- ✓ ≥1 property-based test (hypothesis with ≥10 generated cases)
- ✓ ≥1 real-repo scan test (uses actual codebase, not mocks)

**Updated Checklist:**
```
- [ ] ≥1 test per acceptance criterion
- [ ] Integration tests cover component boundaries
- [ ] Edge cases tested (empty, null, boundary, concurrent)
- [ ] Failure scenarios tested
- [ ] **NEW:** ≥1 property-based test included (hypothesis ≥10 cases)
- [ ] **NEW:** ≥1 real-repo scan test designed (actual codebase, not mocks)
```

### TEST-DESIGNER Role

**NEW:**
- Shadows BUILDER (concurrent, not sequential)
- Includes ≥1 property-based test
- Includes ≥1 real-repo scan test
- Produces test-plan.md with evidence of all three types

### VERIFIER Role

**NEW Pre-flight Phase:**
1. Validate imports: `python -c "import packages.[name]"`
2. Fail fast if broken

**NEW Pilot Phase:**
1. Run 5-10 sample tests from test-plan.md
2. Fail fast if test code syntax broken

**NEW Full Suite Phase:**
1. Run all tests with coverage
2. **NEW:** Verify property-based tests actually ran (≥10 cases per test)
3. **NEW:** Verify real-repo scan results included (not mocks)

---

## Implementation in task-007

**Task-007 spec updated with:**
- AC1: IncrementalIndexer (12+ tests)
- AC2: ortho scan command (8+ tests)
- **AC3: Real-Repo Scan Verification (NEW)**
  - `test_scan_fastapi_real_repo()` — scan fastapi, verify ≥500 symbols
  - `test_call_graph_invariant_property()` — property test, ≥10 cases
- AC4: Zero Regressions

**Test Metrics Expected:**
- Unit tests: 12+ (incremental indexing, scan command)
- Property tests: 1+ (call graph acyclic invariant)
- Real-repo tests: 1+ (fastapi scan)
- Regression tests: ≥30 (task-006 baseline)
- **Total: 45+ tests**
- **Expected coverage: ≥80%**
- **Expected pass rate: 100%**

---

## Adoption Timeline

| Phase | Enforcement |
|-------|------------|
| **Tasks 1–6** | Pre-policy (tests designed, not always executed) |
| **Tasks 7+** | Property-based tests required + real-repo scans required |
| **Immediate** | Workflow `.ases/workflows/feature.md` updated |

---

## References

- **Workflow Update:** `.ases/workflows/feature.md` (GATE 4, TEST-DESIGNER, VERIFIER sections)
- **Task-007 Spec:** `.ases/tasks/task-007-incremental-indexing/spec.md` (AC3, test strategy)
- **Real Repos Location:** `C:\Users\urbra\OneDrive\Desktop\Projects\ortho\Repos\`

---

## Next Steps

1. ✅ Workflow updated (feature.md)
2. ✅ Task-007 spec created with property-based + real-repo tests
3. ⏭️ Human reviews task-007 spec (GATE 1 approval)
4. ⏭️ ARCHITECT reviews architecture (GATE 2)
5. ⏭️ BUILDER implements with TEST-DESIGNER shadowing
6. ⏭️ VERIFIER confirms property tests ran, real-repo scan executed
7. ⏭️ REVIEWER approves

---

*Created by PLANNER on 2026-07-01*  
*Enforced for all Phase 2+ tasks (task-007 onward)*
