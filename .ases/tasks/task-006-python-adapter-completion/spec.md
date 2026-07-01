# task-006: Specification
## Complete Python Language Adapter (CallGraphBuilder, ModuleDetector, ImportGraphBuilder, SymbolExtractor)

**Task ID:** task-006  
**Phase:** 1 Completion (Weeks 3–4)  
**Objective:** Complete Python adapter by removing 28 xfail markers and implementing missing functionality in call graph, module detection, import graph, and symbol extraction.

---

## Objective Statement

Implement missing logic in four Python language adapter components so that all 88 tests in `packages/repo-intelligence/tests/` pass without xfail markers. The adapter must correctly extract function calls, imports, module structure, and symbols from Python source code to support incremental indexing and the `ortho scan` command.

---

## What This Task Covers (In Scope)

1. **CallGraphBuilder** — Build directed graph of function calls
   - Detect function-to-function calls
   - Detect method calls (instance and class methods)
   - Detect nested calls
   - Handle async functions and await expressions
   - Assign confidence scores
   - Provide line numbers for call sites

2. **ImportGraphBuilder** — Extract import relationships
   - Fix remaining edge case (simple import extraction)
   - Ensure syntax error handling

3. **ModuleDetector** — Identify logical modules
   - Detect regular packages (with `__init__.py`)
   - Detect namespace packages (PEP-420, no `__init__.py`)
   - Detect single-module files
   - Handle deep directory nesting
   - Handle symlinks explicitly (skip or resolve)

4. **SymbolExtractor** — Extract symbols from AST
   - Fix line number accuracy (start_line, end_line)
   - Handle unicode in variable names and docstrings
   - Handle syntax errors gracefully

---

## What This Task Does NOT Cover (Out of Scope)

- ❌ Test design or test writing (separate task: TEST-DESIGNER)
- ❌ Verification/running tests (separate task: VERIFIER)
- ❌ Architecture review (waived for this task — internal completion)
- ❌ TypeScript language adapter (Phase 2)
- ❌ Performance optimization (only if tests slow down >2x)
- ❌ New database schema changes
- ❌ Changes to public API contracts (expand existing, don't break)

---

## Input Specification

### Source of Truth
- FRD Section 6 (Pillar 1 — Repository Intelligence)
- QUICK-START-PHASE-2.md (Week 3–4 objectives)
- Current test suite: `packages/repo-intelligence/tests/`
- Existing implementation: `packages/repo-intelligence/src/`

### What Already Works
- SymbolExtractor basic extraction (functions, classes, methods)
- ImportGraphBuilder 95% done (19 xpassed, 1 xfail)
- ModuleDetector 75% done (12 xpassed, 4 xfail)
- Tree-sitter AST parsing (working)
- SQLite storage layer (ready to use)

### What Needs Implementation
- **CallGraphBuilder:** 0% complete (stub only, all 17+ tests xfail)
- **ImportGraphBuilder:** 95% complete (1 xfail to fix)
- **ModuleDetector:** 75% complete (4 xfail to fix)
- **SymbolExtractor:** 85% complete (2 xfail to fix)

---

## Output Specification

### Production Code

**File: `packages/repo-intelligence/src/call_graph.py`**

```python
class CallGraphBuilder:
    """
    Extract function call relationships from Python AST.
    
    Public API:
    - extract_calls(file_path: Path, source: str, symbols: list[Symbol]) -> list[CallEdge]
    """
    
    def extract_calls(
        self,
        file_path: Path,
        source: str,
        symbols: list[Symbol]
    ) -> list[CallEdge]:
        """
        Extract all function calls from source code via static AST analysis.
        
        Returns:
            List of CallEdge with:
            - caller_id: Symbol ID of calling function/method
            - callee_id: Symbol ID of called function/method
            - call_site_line: Line number where the call occurs
            - confidence: 0.0-1.0 score indicating certainty of the call relationship
        
        Handles:
        - Simple function calls: foo()
        - Method calls: obj.method(), self.method()
        - Nested calls: foo(bar())
        - Async/await: async def, await expr
        - Built-in calls: len(), print(), dict()
        - Syntax errors: Log error and skip file gracefully
        
        Static analysis limitations (return lower confidence scores):
        - Dynamic calls (getattr, exec, eval) — runtime-determined
        - Monkey-patched methods — runtime modifications
        - Ambiguous receivers — cannot statically resolve obj.method()
        
        Confidence Score Semantics:
        - 1.0: Exact AST-resolved call (e.g., simple foo() to def foo)
        - 0.9–0.8: Confidently resolved method call (e.g., self.method)
        - 0.7–0.6: Partially inferred call (e.g., obj.method where obj type uncertain)
        - 0.5–0.4: Ambiguous or builtin call (e.g., len(), dict())
        - Below 0.4: Dynamic/runtime-dependent calls not included
        
        Note: Confidence represents static analysis certainty, not runtime correctness.
        """
```

**File: `packages/repo-intelligence/src/import_graph.py`**

Minimal changes — fix edge case in simple import extraction. Signature unchanged.

**File: `packages/repo-intelligence/src/module_detector.py`**

```python
class ModuleDetector:
    """
    Detect logical modules from file system structure.
    
    Public API:
    - detect_modules(root_path: Path) -> list[Module]
    
    Detects:
    - Regular packages (with __init__.py)
    - Namespace packages (PEP-420, no __init__.py)
    - Single .py modules
    - Complex hierarchies (a/b/c/module.py)
    """
```

**File: `packages/repo-intelligence/src/symbol_extractor.py`**

Minor changes — fix line number tracking and unicode handling.

---

## Acceptance Criteria (AC)

### AC1: CallGraphBuilder Functionality
**Test coverage:** 18 tests  
- `test_extract_simple_call` — detects `f()`
- `test_extract_method_calls` — detects `obj.method()` and `self.method()`
- `test_call_from_method` — caller is a method, not just function
- `test_call_line_numbers` — line numbers accurate
- `test_empty_file_no_calls` — returns []
- `test_file_with_only_definitions` — returns []
- `test_syntax_error_handling` — graceful (don't raise, return [])
- `test_nonexistent_file` — graceful error handling
- `test_edge_has_required_fields` — all CallEdges have caller_id, callee_id, call_site_line, confidence
- `test_caller_not_empty` — caller_id is non-empty
- `test_callee_not_empty` — callee_id is non-empty
- `test_detect_nested_calls` — detects foo(bar())
- `test_multiple_calls_same_function` — multiple calls counted separately
- `test_builtin_calls` — len(), print(), dict() detected
- `test_self_method_calls` — self.method() detected
- `test_instance_method_calls` — obj.method() detected
- `test_async_function_calls` — calls within async def
- `test_await_calls` — await expr detected as call

**Verdict:** All 18 tests PASS (EXIT 0), no xfail needed

---

### AC2: ImportGraphBuilder Completion
**Test coverage:** 2 tests
- `test_extract_simple_import` — currently xfail, must pass
- `test_syntax_error_handling` — currently xfail, must pass

**Verdict:** Both tests PASS, no xfail needed

---

### AC3: ModuleDetector Completion
**Test coverage:** 5 tests
- `test_detect_regular_package` — `__init__.py` detected
- `test_single_module_detection` — `.py` file detected as module
- `test_submodule_names` — submodule names accurate
- `test_deep_nesting` — `a/b/c/d/module.py` traversed
- `test_symlink_handling` — handled or explicitly skipped

**Verdict:** All 5 tests PASS, no xfail needed

---

### AC4: SymbolExtractor Completion
**Test coverage:** 2 tests
- `test_symbol_line_numbers` — start_line, end_line accurate
- `test_unicode_content` — unicode names and docstrings

**Verdict:** Both tests PASS, no xfail needed

---

### AC5: Zero Regressions

**Regression verification:**

1. `pytest packages/repo-intelligence/tests/ -v --tb=short`  
   Expected: All previously passing tests continue to pass

2. `pytest -v --tb=short` (all packages)  
   Expected: No new test failures introduced by these changes

A regression is defined as a previously passing test now failing due to changes in this task.

---

## Interface Contracts

All methods return stable types defined in shared types:

```python
# Input
Symbol  # From symbol_extractor.py (existing)
Path    # pathlib.Path

# Output
CallEdge:
    caller_id: str          # Symbol ID (hash)
    callee_id: str          # Symbol ID (hash) — may be external string if unresolved
    call_site_line: int     # Line number
    confidence: float       # 0.0-1.0

ImportEdge:
    importer_file_id: str
    imported_file_id: str | None
    imported_module: str
    is_external: bool
    symbols_imported: list[str]

Module:
    id: str
    path: Path
    name: str
    is_package: bool        # True if __init__.py exists
    is_namespace: bool      # True if PEP-420
    submodules: list[Module]
```

No changes to these contracts — only expansion of existing implementations.

---

## Data Flow

```
Python source file
    ↓
Tree-sitter AST parse (existing)
    ↓
CallGraphBuilder.extract_calls() → CallEdge[]
ImportGraphBuilder.extract_imports() → ImportEdge[]
SymbolExtractor.extract_symbols() → Symbol[]
    ↓
ModuleDetector.detect_modules() → Module[]
    ↓
Stored in SQLite (existing storage layer)
```

---

## Quality Metrics (Monitored, Not Gate-Blocking)

The following metrics are tracked and reported but do **not** determine acceptance:

### Code Coverage

- **Measured:** Line coverage of modified files (`call_graph.py`, `import_graph.py`, `module_detector.py`, `symbol_extractor.py`)
- **Target:** ≥85% (informational)
- **Purpose:** Identifies untested code paths
- **Not a gate:** Acceptance determined by AC1–AC5, not coverage percentage

If coverage falls short, VERIFIER reports it but merge is not blocked.

### Lint Compliance

- **Measured:** `ruff check packages/repo-intelligence/`
- **Target:** EXIT 0 (no lint violations)
- **Purpose:** Code style consistency
- **Not a hard gate:** Style violations should be addressed, but acceptance depends on AC1–AC5

### Type Checking

- **Measured:** `mypy --strict packages/repo-intelligence/`
- **Target:** EXIT 0 (no type errors)
- **Purpose:** Static type safety
- **Not a hard gate:** Type errors should be addressed, but acceptance depends on AC1–AC5

### Performance Baseline

- **Measured:** Execution time for `pytest packages/repo-intelligence/tests/` before and after
- **Purpose:** Detect performance regressions
- **Not a gate:** Unless execution time increases >2x (then escalate to BUILDER)

---

## Test Verification Strategy

The task will be verified using the existing test suite (88 tests total):

- **CallGraphBuilder tests:** 18 tests covering function calls, methods, nested calls, async, built-ins, edge cases
- **ImportGraphBuilder tests:** 20 tests (19 currently passing, 1 to fix)
- **ModuleDetector tests:** 16 tests (12 currently passing, 4 to fix)
- **SymbolExtractor tests:** 15 tests (13 currently passing, 2 to fix)
- **Other tests:** 19 tests (basic integration and adapter interface tests)

**Regression coverage:** All 88 tests must execute and pass (or maintain baseline status if legitimately incomplete)

---

## Known Limitations & Deferrals

All acceptance criteria (AC1–AC5) are within scope and must be implemented.

If the BUILDER discovers legitimate limitations during implementation:

1. **Document immediately in implementation-notes.md** with:
   - What was attempted
   - Why it could not be completed
   - Technical explanation of the blocker
   - Upgrade path (how to complete in future)

2. **Mark affected tests** with `@pytest.mark.xfail(reason="documented limitation")` ONLY if:
   - The limitation is genuine and documented in implementation-notes.md
   - PLANNER approved the limitation in this spec (before BUILDER started)
   - The xfail reason is specific and non-vague

3. **Report to human at GATE 3** (Scope Review) so human can approve the limitation

If a limitation is discovered without prior approval, BUILDER must attempt to complete the feature or report the blocker to PLANNER for re-planning.

---

## Definition of Done

1. ✓ All acceptance criteria (AC1–AC5) implemented and verified via pytest
2. ✓ All tests execute via pytest (no design-only tests, all results are real)
3. ✓ No regressions in other test suites (all packages)
4. ✓ implementation-notes.md documents:
   - What was built (one section per AC)
   - Any deviations from spec with justification
   - Any limitations with documented rationale
5. ✓ Human approves scope at GATE 3 (no unexpected modifications)
6. ✓ VERIFIER runs tests and produces evidence logs (test-*.log files with exit codes)
7. ✓ Quality metrics reviewed (coverage, lint, types documented but not blocking)
8. ✓ REVIEWER approves code quality and behavior
9. ✓ Merged to main with evidence reference in commit message

---

---

## Confidence Score Reference (CallGraphBuilder)

Every CallEdge returned by CallGraphBuilder includes a confidence score (0.0–1.0) indicating the certainty of the call relationship as determined by static AST analysis.

### Confidence Bands and Interpretations

| Band | Range | Meaning | Examples |
|------|-------|---------|----------|
| **Certain** | 1.0 | Exact AST-resolved call with perfect certainty | `foo()` where `def foo` found in same scope |
| **High** | 0.9–0.8 | Confidently resolved call, minimal ambiguity | `self.method()` within a class, instance method calls with clear receiver |
| **Moderate** | 0.7–0.6 | Partially inferred call with structural support | `obj.method()` where obj type is somewhat uncertain but method exists |
| **Low** | 0.5–0.4 | Ambiguous or builtin call, static analysis limits | `len()`, `dict()`, dynamic attribute access, calls with unclear receivers |
| **Very Low** | Below 0.4 | Dynamic/runtime-dependent, not reliably resolved | `exec()`, `getattr()`, monkey-patched methods — NOT returned |

### What Confidence Represents

- **Certainty of static resolution:** How confidently the AST analysis can determine that a call exists and connect caller to callee
- **NOT runtime correctness:** A high-confidence call may fail at runtime; a low-confidence call may execute successfully
- **NOT frequency or importance:** Confidence does not indicate how often a function is called or how critical it is

### BUILDER Implementation Guidance

When assigning confidence scores:
1. Start with 1.0 for simple cases (`foo()` where `def foo` exists)
2. Reduce confidence when:
   - Receiver type is ambiguous (`obj.method()` where obj is a parameter)
   - Call is to a builtin or external function
   - Resolution required inference rather than direct AST matching
3. Never return confidence below 0.4 (skip those calls entirely)
4. Document confidence assignment logic in code comments

### VERIFIER Validation

Confidence scores do not need to match specific numbers perfectly — focus on:
- Presence of confidence field (always populated, never None)
- Range 0.0–1.0 (never outside bounds)
- Reasonable ordering (more certain calls score higher)

Confidence score disagreements should not block merge if calls are correctly identified.

---

*Created by PLANNER*  
*Status: DRAFT → awaiting human approval at GATE 1*
