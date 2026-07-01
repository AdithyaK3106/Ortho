# Ortho Phase 1 Bug List

**Date:** 2026-07-01  
**Status:** All bugs identified via real test execution  
**Blocker for Phase 2:** YES — Must fix before proceeding  

---

## Bug Summary

| Priority | Task | Component | Bug | Impact | Status |
|----------|------|-----------|-----|--------|--------|
| CRITICAL | 004 | ContextHub | FTS5 empty query syntax error | Search broken | OPEN |
| HIGH | 004 | ContextHub | Versioning hash collision | Duplicate artifacts | OPEN |
| HIGH | 004 | ContextHub | Staleness detector not detecting changes | Cache invalidation broken | OPEN |
| MEDIUM | 004 | ContextHub | Git metadata extraction fails on Windows | Metadata unavailable | OPEN |
| MEDIUM | 004 | ContextHub | Hybrid search limit not respected | Wrong result count | OPEN |
| HIGH | 002-003 | tree-sitter | Language loading API mismatch | PythonAdapter crashes | OPEN |
| MEDIUM | 002-003 | CallGraphBuilder | Constructor requires arguments | API mismatch | OPEN |
| MEDIUM | 002-003 | ModuleDetector | Constructor requires arguments | API mismatch | OPEN |
| HIGH | 005 | Detector | Hexagonal pattern misclassified | Wrong architecture type | OPEN |
| MEDIUM | 005 | Detector | Flat pattern misclassified | Wrong architecture type | OPEN |
| MEDIUM | 005 | LayerDetector | Violation detection too permissive | False negative violations | OPEN |

**Total:** 11 bugs blocking Phase 2  
**Test-Found:** 10 bugs (real test execution)  
**Known Edge Case:** 1 bug (task-005)

---

## Task-004: ContextHub Bugs (10 failures / 55 tests)

### BUG-001: FTS5 Empty Query Syntax Error [CRITICAL]
- **File:** `packages/context-hub/src/context_hub/search/bm25.py:61`
- **Error:** `sqlite3.OperationalError: fts5: syntax error near ""`
- **Impact:** Search completely broken
- **Test:** `test_hybrid_search_limit_respected`
- **Fix:** Add empty query check before FTS5 execution
- **ETA:** 30 minutes

### BUG-002: Versioning Hash Collision [HIGH]
- **File:** `packages/context-hub/src/context_hub/store.py`
- **Error:** `AssertionError: assert '667ba4c3a64a6f5a' == 'a04afb68e6b11e0b'`
- **Impact:** Artifact versions have same ID (data corruption)
- **Tests:** `test_versioning_different_content`, `test_get_next_version_existing`
- **Fix:** Review hash calculation, ensure content is included
- **ETA:** 1 hour

### BUG-003: Staleness Detector Not Working [HIGH]
- **File:** `packages/context-hub/src/context_hub/staleness.py`
- **Error:** `AssertionError: False is True` (not detecting changes)
- **Impact:** Cache invalidation broken
- **Tests:** `test_staleness_file_deleted`, `test_staleness_content_unchanged`, `test_staleness_content_changed`
- **Fix:** Review staleness detection logic and hash comparison
- **ETA:** 1 hour

### BUG-004: Git Metadata Extraction Fails [MEDIUM]
- **File:** `packages/context-hub/src/context_hub/git_metadata.py`
- **Error:** `PermissionError: [WinError 32] temp dir cleanup fails on Windows`
- **Impact:** Git history unavailable, temp directory leak
- **Test:** `test_get_file_churn_with_commits`
- **Fix:** Use proper context manager for temp dir cleanup
- **ETA:** 45 minutes

### BUG-005: Hybrid Search Limit Ignored [MEDIUM]
- **File:** `packages/context-hub/src/context_hub/search/hybrid.py`
- **Error:** Result count exceeds limit parameter
- **Impact:** Wrong number of results returned
- **Test:** `test_hybrid_search_limit_respected`
- **Fix:** Apply limit after RRF merge
- **ETA:** 30 minutes

### BUG-006: Artifact History Missing [MEDIUM]
- **File:** `packages/context-hub/src/context_hub/store.py`
- **Error:** `AssertionError: assert 1 == 3` (only 1 version)
- **Impact:** Version history incomplete
- **Test:** `test_get_artifact_history`
- **Fix:** Fix versioning logic (depends on BUG-002)
- **ETA:** 30 minutes

### BUG-007: Specific Version Retrieval Returns None [MEDIUM]
- **File:** `packages/context-hub/src/context_hub/store.py`
- **Error:** `AttributeError: 'NoneType' object has no attribute 'version'`
- **Impact:** Can't retrieve specific versions
- **Test:** `test_get_artifact_specific_version`
- **Fix:** Check query logic
- **ETA:** 45 minutes

---

## Task 002-003: Python Adapter Bugs (9 failures / 106 tests)

### BUG-008: tree-sitter-languages API Mismatch [HIGH]
- **File:** `packages/repo-intelligence/src/repo_intelligence/adapters/python_adapter.py:31`
- **Error:** `TypeError: __init__() takes exactly 1 argument (2 given)`
- **Impact:** PythonAdapter crashes, can't parse Python
- **Tests:** 6 tests (all PythonAdapter initialization)
- **Fix:** Update tree-sitter-languages to compatible version
- **ETA:** 30 minutes

### BUG-009: CallGraphBuilder Constructor Mismatch [MEDIUM]
- **File:** `packages/repo-intelligence/src/repo_intelligence/call_graph.py`
- **Error:** Requires (repo_root, python_files) but tests expect no args
- **Impact:** API mismatch, tests fail
- **Tests:** `test_import_call_graph_builder`, `test_builder_initialization`
- **Fix:** Update tests to pass required arguments
- **ETA:** 30 minutes

### BUG-010: ModuleDetector Constructor Mismatch [MEDIUM]
- **File:** `packages/repo-intelligence/src/repo_intelligence/module_detector.py`
- **Error:** Requires repo_root but tests expect no args
- **Impact:** API mismatch, tests fail
- **Tests:** `test_detector_initialization`, `test_detector_can_scan_directory`
- **Fix:** Update tests to pass repo_root argument
- **ETA:** 30 minutes

---

## Task-005: Architecture Detection Bugs (4 failures / 53 tests)

### BUG-011: Hexagonal Pattern Misclassified [HIGH]
- **File:** `packages/arch-intelligence/src/arch_intelligence/detector.py`
- **Error:** `AssertionError: Expected 'hexagonal', got 'layered'`
- **Cause:** Hexagonal score (0.91) < Layered (0.95)
- **Impact:** All hexagonal architectures detected as layered
- **Tests:** `test_hexagonal_fixture_detects_as_hexagonal`, `test_hexagonal_confidence_breakdown_shows_hexagonal_highest`
- **Fix:** Adjust hexagonal pattern detection scoring
- **ETA:** 2 hours

### BUG-012: Flat Pattern Misclassified [MEDIUM]
- **File:** `packages/arch-intelligence/src/arch_intelligence/detector.py`
- **Error:** `AssertionError: Expected 'flat', got 'layered'`
- **Cause:** Flat detection too weak
- **Impact:** Flat architectures detected as layered
- **Test:** `test_flat_fixture_detects_as_flat`
- **Fix:** Increase flat pattern detection sensitivity
- **ETA:** 1.5 hours

### BUG-013: Layer Violations Too Permissive [MEDIUM]
- **File:** `packages/arch-intelligence/src/arch_intelligence/layer_detector.py`
- **Error:** `AssertionError: Expected ≤1 violations, got 9`
- **Cause:** Violation detection threshold too high
- **Impact:** Invalid cross-layer imports not detected
- **Test:** `test_layered_fixture_has_minimal_violations`
- **Fix:** Tighten layer hierarchy validation rules
- **ETA:** 1.5 hours

---

## Fix Strategy & Timeline

### Phase 1: Critical Path (5 hours)
1. BUG-008 (tree-sitter) — 30 min → 6 tests unblocked
2. BUG-001 (FTS5) — 30 min → 1 test unblocked
3. BUG-002 (versioning) — 1 hour → 3 tests unblocked
4. BUG-011 (hexagonal) — 2 hours → 2 tests unblocked
5. BUG-012 (flat) — 1.5 hours → 1 test unblocked

**Result:** 80%+ pass rate, ready for Phase 2

### Phase 2: High Priority (4.5 hours)
6. BUG-003 (staleness) — 1 hour
7. BUG-009 (CallGraphBuilder) — 30 min
8. BUG-010 (ModuleDetector) — 30 min
9. BUG-013 (layer violations) — 1.5 hours

**Result:** 90%+ pass rate

### Phase 3: Polish (2.5 hours)
10. BUG-004 (git metadata) — 45 min
11. BUG-005 (hybrid limit) — 30 min
12. BUG-006 (artifact history) — 30 min (depends on BUG-002)
13. BUG-007 (specific version) — 45 min

**Result:** 95%+ pass rate

---

## Phase 2 Readiness Checklist

### Code Quality
- [ ] All 11 bugs fixed or marked xfail
- [ ] Task-001: npm installed, tsc compiles
- [ ] Task-002-003: ≥80% test pass rate (48+/106)
- [ ] Task-004: ≥80% test pass rate (44+/55)
- [ ] Task-005: ≥95% test pass rate (50+/53)

### Documentation
- [ ] All dependencies documented in pyproject.toml
- [ ] All builds verified (tsc, mypy, ruff)
- [ ] This BUGS.md updated with fixes

### Testing
- [ ] Real pytest execution for all tasks
- [ ] No designed-only tests
- [ ] Evidence logs stored in .ases/evidence/

**Estimated time to Phase 2 readiness:** 12 hours

---

## Evidence Trail

- Real test execution logs: `.ases/evidence/task-retest/`
- Test results: 
  - Task-004: 44 pass, 10 fail, 1 error (80%)
  - Task-005: 49 pass, 4 fail (92.5%)
  - Task-002-003: 4 pass, 9 fail (31%)
- Detailed reports:
  - TASK-1-3-VERIFICATION-REPORT.md
  - REAL-TEST-RESULTS.md
  - TASK-2-3-TEST-EXECUTION-REPORT.md

