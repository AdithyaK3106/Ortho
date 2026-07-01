# task-006: Complete Python Adapter
## Feature Plan & Breakdown

**Version:** 1.0  
**Phase:** 1 Completion (Week 3–4 continued)  
**Objective:** Remove 28 xfail markers from repo-intelligence tests by completing CallGraphBuilder, ModuleDetector, ImportGraphBuilder, and SymbolExtractor.

---

## Feature Summary

The Python language adapter is 60% complete. CallGraphBuilder has only stub implementations; ModuleDetector, ImportGraphBuilder, and SymbolExtractor have partial implementations with known failing test cases. This task completes all four components so the adapter can support incremental indexing and the `ortho scan` command in Week 5–6.

**Why now:** CallGraphBuilder and edge cases in other extractors block Week 5–6 (Incremental Indexing). Completing this first unblocks the full pipeline.

---

## Current State (Baseline)

From pytest output (88 tests total):
- **CallGraphBuilder:** 1 xpass, 17 xfail (stub, no implementation)
- **ImportGraphBuilder:** 1 xfail, 19 xpassed (95% done, one edge case)
- **ModuleDetector:** 4 xfail, 12 xpassed (mostly done)
- **SymbolExtractor:** 2 xfail, 13 passed (nearly done)
- **Other:** 4 xfail (adapter syntax error, unicode edge case)

**Current implementation status:**
- CallGraphBuilder: 0% complete — stub implementation only
- ImportGraphBuilder: 95% complete — one edge case behavior missing
- ModuleDetector: 75% complete — namespace detection and complex hierarchies incomplete
- SymbolExtractor: 85% complete — line number accuracy and unicode handling incomplete

**Test execution policy:** MANDATORY (Phase 2+) — all tests must run via pytest, no design-only tests.

---

## Atomic Tasks (in order)

### Atomic Task 1: CallGraphBuilder — Basic Call Extraction
**Scope:** Implement simple function-to-function call detection  
**Files:** `packages/repo-intelligence/src/call_graph.py`  
**Tests:** `test_extract_simple_call`, `test_extract_file_with_only_definitions`, `test_nonexistent_file`  
**Time:** 45 min

**AC:**
- [x] AST traversal detects function calls via `Call` nodes
- [x] Returns list of CallEdge with caller_id, callee_id, call_site_line
- [x] Handles empty files (returns [])
- [x] Handles files with no calls (returns [])
- [x] Handles nonexistent files (raises error or returns [])

---

### Atomic Task 2: CallGraphBuilder — Method and Nested Calls
**Scope:** Detect method calls (`self.x()`, `obj.method()`) and nested calls  
**Files:** `packages/repo-intelligence/src/call_graph.py`  
**Tests:** `test_extract_method_calls`, `test_call_from_method`, `test_detect_nested_calls`, `test_multiple_calls_same_function`  
**Time:** 60 min

**AC:**
- [x] Detects `self.method()` calls from within methods
- [x] Detects instance method calls (`obj.method()`)
- [x] Detects nested calls (calls within calls)
- [x] Tracks line numbers for each call site
- [x] Returns correct caller/callee for methods

---

### Atomic Task 3: CallGraphBuilder — Built-in and Async Calls
**Scope:** Handle built-in calls, async functions, and await expressions  
**Files:** `packages/repo-intelligence/src/call_graph.py`  
**Tests:** `test_builtin_calls`, `test_self_method_calls`, `test_instance_method_calls`, `test_async_function_calls`, `test_await_calls`  
**Time:** 50 min

**AC:**
- [x] Detects calls to built-in functions (`len()`, `print()`, `dict()`)
- [x] Detects calls within async functions
- [x] Detects `await` expressions as calls
- [x] Confidence score reflects call type (built-in may be lower confidence)
- [x] Edge cases: line numbers accurate for all call types

---

### Atomic Task 4: CallGraphBuilder — Edge Cases and Error Handling
**Scope:** Handle syntax errors, malformed AST, confidence scoring  
**Files:** `packages/repo-intelligence/src/call_graph.py`  
**Tests:** `test_syntax_error_handling`, `test_call_line_numbers`, `test_edge_has_required_fields`, `test_caller_not_empty`, `test_callee_not_empty`  
**Time:** 40 min

**AC:**
- [x] Syntax errors handled gracefully (skip file or return [] with error logged)
- [x] All returned CallEdges have required fields (caller_id, callee_id, call_site_line, confidence)
- [x] caller_id and callee_id are non-empty strings
- [x] Confidence is 0.0–1.0
- [x] Line numbers are accurate and non-zero

---

### Atomic Task 5: ImportGraphBuilder — Edge Cases
**Scope:** Fix remaining 1 xfail (simple import extraction)  
**Files:** `packages/repo-intelligence/src/import_graph.py`  
**Tests:** `test_extract_simple_import`, `test_syntax_error_handling`  
**Time:** 25 min

**AC:**
- [x] `import x` statements extracted as ImportEdge
- [x] `from x import y` statements extracted
- [x] Syntax errors handled gracefully
- [x] Line numbers accurate

---

### Atomic Task 6: ModuleDetector — Complete
**Scope:** Implement namespace package and complex hierarchy detection  
**Files:** `packages/repo-intelligence/src/module_detector.py`  
**Tests:** `test_detect_regular_package`, `test_single_module_detection`, `test_submodule_names`, `test_deep_nesting`, `test_symlink_handling`  
**Time:** 45 min

**AC:**
- [x] Detects regular packages (with `__init__.py`)
- [x] Detects namespace packages (no `__init__.py`, PEP-420)
- [x] Single `.py` file detected as module
- [x] Deep nesting (`a/b/c/d/module.py`) traversed correctly
- [x] Symlinks handled or explicitly skipped
- [x] Module properties (path, name, submodules) accurate

---

### Atomic Task 7: SymbolExtractor — Edge Cases
**Scope:** Fix line numbers and unicode handling  
**Files:** `packages/repo-intelligence/src/symbol_extractor.py`  
**Tests:** `test_symbol_line_numbers`, `test_file_with_syntax_error`, `test_unicode_content`  
**Time:** 30 min

**AC:**
- [x] Symbol start_line and end_line accurately reflect source positions
- [x] Syntax errors handled gracefully
- [x] Unicode variable names and docstrings extracted correctly
- [x] No silent failures; errors logged with context

---

### Atomic Task 8: Integration and Regression Verification
**Scope:** Verify all behavior implemented and no regressions introduced  
**Files:** No new files (verification only)  
**Tests:** All 88 tests in repo-intelligence  
**Time:** 30 min

**AC:**
- [x] All tests in `pytest packages/repo-intelligence/tests/ -v` execute (real test results, not design-only)
- [x] Previously passing tests continue to pass (zero new failures)
- [x] All previously failing tests from Tasks 1–7 now pass
- [x] No regressions in other packages (`pytest` full suite shows same baseline or better)

---

## Files to Modify

| File | Change | Scope |
|------|--------|-------|
| `packages/repo-intelligence/src/call_graph.py` | Complete implementation (all methods) | ~400 lines new code |
| `packages/repo-intelligence/src/import_graph.py` | Fix 1 edge case | ~20 lines modified |
| `packages/repo-intelligence/src/module_detector.py` | Complete namespace detection | ~100 lines new code |
| `packages/repo-intelligence/src/symbol_extractor.py` | Fix edge cases | ~50 lines modified |

## Files to Create

None — only modifications to existing stubs.

## Files to NOT Touch

- `packages/repo-intelligence/tests/` (test design is separate task)
- `packages/context-hub/`
- `packages/arch-intelligence/`
- `apps/cli/`, `apps/api-server/`
- Any TypeScript files

---

## Task Dependencies

This task has **no external dependencies**. It completes internal work blocked only by missing implementations.

**Blocked by:** Nothing  
**Blocks:** task-007 (Incremental Indexing + `ortho scan`)

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| AST parsing edge cases (decorators, comprehensions) | Medium | Incomplete call graph | Test-driven: design tests first, implement to pass |
| Line number tracking inaccuracy | Medium | Hard to debug call chains | Validate with actual Python source positions |
| Confidence scoring is subjective | Low | Results feel arbitrary | Document confidence semantics in code |
| Performance regression (slow indexing) | Low | Week 5–6 blocked | Benchmark before/after if tests slow down |

---

## Acceptance Criteria (Binary & Testable)

### AC1: CallGraphBuilder Behavior Implemented

The implementation must demonstrate these capabilities via passing tests:

1. **Simple function call detection:** `f()` correctly identified with caller, callee, line number
2. **Method call detection:** `obj.method()` and `self.method()` correctly identified
3. **Nested call detection:** `foo(bar())` correctly identified as two separate calls
4. **Async function support:** Calls within async functions and await expressions correctly identified
5. **Built-in call handling:** Calls to `len()`, `print()`, `dict()` identified with appropriate confidence
6. **Line number accuracy:** All returned calls have accurate call_site_line values
7. **Edge case handling:** Gracefully handles empty files, files with no calls, syntax errors
8. **Output format:** All CallEdge objects have required fields (caller_id, callee_id, call_site_line, confidence)

**Verification:** All CallGraphBuilder tests execute and pass via `pytest`.

### AC2: ImportGraphBuilder Edge Cases Resolved

The implementation must demonstrate:

1. **Simple import extraction:** `import x` statements correctly extracted
2. **Syntax error handling:** Gracefully handles malformed Python without raising exceptions

**Verification:** Previously failing ImportGraphBuilder tests now pass.

### AC3: ModuleDetector Complete

The implementation must demonstrate:

1. **Regular package detection:** Directories with `__init__.py` correctly identified
2. **Namespace package support (PEP-420):** Directories without `__init__.py` correctly identified
3. **Single module detection:** Standalone `.py` files correctly identified as modules
4. **Hierarchical traversal:** Deep nesting (e.g., `a/b/c/d/module.py`) correctly traversed
5. **Symlink handling:** Symlinks explicitly handled (either followed or skipped with documentation)

**Verification:** All ModuleDetector tests execute and pass.

### AC4: SymbolExtractor Edge Cases Resolved

The implementation must demonstrate:

1. **Accurate line tracking:** Symbol start_line and end_line correctly reflect source positions
2. **Unicode support:** Variable names and docstrings with unicode characters correctly extracted
3. **Error handling:** Syntax errors handled gracefully

**Verification:** SymbolExtractor tests execute and pass.

### AC5: Zero Regressions

Verification shows no new test failures in the full pytest suite across all packages.

**Verification:** `pytest` (all packages) shows same or fewer failures than baseline.

### AC6: Implementation Completeness

BUILDER produces implementation-notes.md documenting:
- What was implemented
- What was NOT implemented (if any)
- Any deviations from this plan with justification

---

## Rollback Scenario

See rollback-plan.md (linked artifact).

---

## Quality Metrics (Monitored, Not Gate-Blocking)

The following metrics are tracked and reported but do not determine acceptance or block merge:

| Metric | Target | Purpose | Blocking If |
|--------|--------|---------|------------|
| **Code coverage** | ≥85% | Identify untested paths | No (informational only) |
| **Lint compliance** | `ruff check` EXIT 0 | Code style consistency | No (report but don't block) |
| **Type checking** | `mypy --strict` EXIT 0 | Static type safety | No (report but don't block) |
| **Execution time** | Same or faster than baseline | Performance regression detection | Yes, only if >2x slower (then BUILDER optimizes) |

**Interpretation:** Acceptance is determined by AC1–AC5 (behavior and regressions), not by these supporting metrics. Quality issues are reported and addressed but do not determine feature completion.

---

## Success Criteria (Behavior-Based)

✓ All atomic task behavior implemented as specified in AC1–AC4  
✓ All tests execute via pytest (no design-only tests)  
✓ No regressions in other packages  
✓ implementation-notes.md documents scope and any deviations  
✓ Quality metrics reviewed and documented (even if not all targets met)

---

*Created by PLANNER*  
*Status: DRAFT → awaiting human approval at GATE 1*
