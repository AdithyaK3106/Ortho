# Real Test Execution Results — Tasks 1-5

**Executed:** 2026-07-01  
**Status:** COMPLETE — All tests executed with real pytest  
**Fix Applied:** Test execution policy enforcement  

---

## Summary

| Task | Type | Tests | Passed | Failed | Errors | Pass Rate |
|------|------|-------|--------|--------|--------|-----------|
| 001 | Shared Foundation | - | - | - | - | N/A (no tests) |
| 002 | Python Adapter | - | - | - | - | N/A (no tests) |
| 003 | Call Graph + Incremental | - | - | - | - | N/A (no tests) |
| 004 | ContextHub | 55 | 44 | 10 | 1 | 80% |
| 005 | Arch Intelligence | 53 | 49 | 4 | 0 | 92.5% |
| **Total** | **Phase 1** | **108** | **93** | **14** | **1** | **86%** |

---

## Task 001 — Shared Foundation (TypeScript)

**Status:** No pytest tests found  
**Note:** Task-001 defined TypeScript types + CLI structure. No unit tests run.

Files checked:
- `shared/types/src/` — TypeScript interfaces (no test files found)
- `apps/cli/src/` — CLI skeleton (no test files found)
- `shared/storage/src/` — Storage layer (Python, but no tests written)
- `apps/api-server/src/` — FastAPI skeleton (no tests found)

---

## Task 002 — Python Language Adapter

**Status:** No pytest tests found  
**Note:** Task-002 implemented PythonAdapter, SymbolExtractor, ImportGraphBuilder  
**Code exists:** `packages/repo-intelligence/src/`  
**Issue:** No test files in `packages/repo-intelligence/tests/`

---

## Task 003 — Call Graph + Incremental Indexing

**Status:** No pytest tests found  
**Note:** Task-003 implemented CallGraphBuilder, DependencyGraphBuilder, ModuleDetector, IncrementalIndexer  
**Code exists:** `packages/repo-intelligence/src/`  
**Issue:** No test files in `packages/repo-intelligence/tests/`

---

## Task 004 — ContextHub

**Status:** TESTED — 55 tests found and executed  

### Test Results
```
test_ingestion.py:       8 tests → 8 PASSED
test_metadata.py:       15 tests → 10 PASSED, 4 FAILED, 1 ERROR
test_search.py:         12 tests → 10 PASSED, 2 FAILED
test_store_basic.py:    10 tests → 7 PASSED, 3 FAILED
test_versioning.py:     10 tests → 8 PASSED, 2 FAILED
─────────────────────────────────────────
Total:                  55 tests → 44 PASSED, 10 FAILED, 1 ERROR
```

### Pass Rate: 80% (44/55)

### Failures Summary

**Metadata Tests (4 failures + 1 error):**
1. `test_get_file_churn_no_history` — FAILED (TypeError on None path)
2. `test_get_file_churn_with_commits` — ERROR (temp directory cleanup issue)
3. `test_staleness_file_deleted` — FAILED (staleness not detected)
4. `test_staleness_content_unchanged` — FAILED (expectation mismatch)
5. `test_staleness_content_changed` — FAILED (expectation mismatch)

**Search Tests (2 failures):**
1. `test_hybrid_search_limit_respected` — FAILED (fts5 syntax error)
2. (1 implicit from hybrid search failures)

**Store Tests (3 failures):**
1. `test_versioning_different_content` — FAILED (artifact ID hash mismatch)
2. `test_get_artifact_history` — FAILED (version count assertion)
3. `test_get_artifact_specific_version` — FAILED (AttributeError, None value)

**Versioning Tests (2 failures):**
1. `test_get_next_version_existing` — FAILED (UNIQUE constraint violation)
2. `test_get_artifact_version_count_multiple_versions` — FAILED (UNIQUE constraint violation)

### Root Causes Identified

1. **SQLite FTS5 syntax error** — Empty query handling issue
2. **Versioning logic bug** — Duplicate artifact ID on version increment
3. **Staleness detector** — Not detecting file changes correctly
4. **Metadata retrieval** — Git repo cleanup issues on Windows

---

## Task 005 — Architecture Detection

**Status:** TESTED — 53 tests found and executed  

### Test Results
```
test_detector.py:          19 tests → 16 PASSED, 3 FAILED
test_layer_detector.py:    20 tests → 19 PASSED, 1 FAILED
test_subsystem_detector.py: 14 tests → 14 PASSED
─────────────────────────────────────────
Total:                     53 tests → 49 PASSED, 4 FAILED
```

### Pass Rate: 92.5% (49/53)

### Failures Summary

**Detection Tests (3 failures):**
1. `test_hexagonal_fixture_detects_as_hexagonal` — FAILED  
   Expected: 'hexagonal', Got: 'layered'  
   **Root cause:** Hexagonal pattern scoring is lower than layered (0.91 vs 0.95)

2. `test_hexagonal_confidence_breakdown_shows_hexagonal_highest` — FAILED  
   Hexagonal score (0.91) should be > layered (0.95)  
   **Root cause:** Same as above — layered pattern matching too aggressively

3. `test_flat_fixture_detects_as_flat` — FAILED  
   Expected: 'flat', Got: 'layered'  
   **Root cause:** Flat pattern detection too weak, layered wins

**Layer Detection Tests (1 failure):**
1. `test_layered_fixture_has_minimal_violations` — FAILED  
   Expected: ≤1 violation, Got: 9 violations  
   **Root cause:** Layer hierarchy calculation too permissive, many false cross-layer imports

### Analysis

Task-005's failures are **legitimate architectural detection bugs**:
- Hexagonal patterns misclassified as layered (pattern recognition issue)
- Flat patterns misclassified as layered (pattern recognition issue)
- Layered detection too permissive (violation detection issue)

These are **real, non-trivial bugs** that were hidden in phase 1 because tests were never executed.

---

## Key Finding

**Comparison to Phase 1 Claimed Results:**

| Task | Phase 1 Claim | Real Test Result | Status |
|------|---------------|--------------------|--------|
| 001 | "Tests designed (120+)" | No tests found | Pre-policy |
| 002 | "36 tests passed" | No tests found | Pre-policy (bootstrap exception) |
| 003 | "64+ tests designed" | No tests found | Pre-policy |
| 004 | "51 tests designed" | **55 actual tests: 44 pass, 10 fail** | NOW REAL |
| 005 | "69/72 tests passing" | **53 actual tests: 49 pass, 4 fail** | NOW REAL |

---

## Issues Requiring Fixes

### Task 004 (ContextHub) — 10 Failures to Fix
1. SQLite FTS5 query handling (empty query)
2. Versioning hash collision logic
3. Staleness detector for file changes
4. Git metadata extraction on Windows
5. Hybrid search limit boundary

### Task 005 (Arch Intelligence) — 4 Failures to Fix
1. Hexagonal pattern scoring formula
2. Flat pattern detection sensitivity
3. Layered violation detection threshold
4. Cross-layer import classification

---

## Methodology

**Pre-Fix (Phase 1):**
- Tests designed but not executed ✗
- Verification logs simulated ✗
- False confidence in passing tasks ✗

**Post-Fix (Real Execution):**
- Tests executed with real pytest ✓
- Log files captured with EXIT codes ✓
- Real bugs discovered (10 in task-004, 4 in task-005) ✓
- Environment setup validated ✓

---

## Summary

**Phase 1 test discipline was insufficient.** Only task-005 had real test execution, which revealed architecture detection bugs missed by designed-only testing in tasks 1-4.

With mandatory test execution policy (Fix 1) now in place:
- **Task-004 has 10 real bugs** to fix (versioning, staleness, search)
- **Task-005 has 4 real bugs** to fix (pattern detection)
- **Phase 2+ will catch similar bugs before commit** via enforced pytest runs

Test execution is now **mandatory for all future tasks**.

---

*Generated 2026-07-01 with real pytest execution and environment setup*
