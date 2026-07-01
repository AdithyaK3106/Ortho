# task-007: Specification
## Incremental Indexing + ortho scan Integration

**Task ID:** task-007  
**Phase:** 1 Continued (Weeks 5–6)  
**Objective:** Integrate Python adapter components into `ortho scan` command with incremental indexing (git diff based), real-repo scanning, and property-based test coverage.

---

## Objective Statement

Implement `ortho scan` command that:
1. Scans a Python repository completely (discovers all modules, symbols, call graphs, imports)
2. Stores results in SQLite with git metadata
3. Updates incrementally (detects changed files via git diff, re-indexes only what changed)
4. Verifies correctness against real codebase (fastapi) using property-based tests + real-repo scan

---

## What This Task Covers (In Scope)

1. **IncrementalIndexer** — git diff based re-indexing
   - Detect changed files (git diff HEAD~1)
   - Re-index only changed files + affected dependencies
   - Preserve unchanged symbol registry

2. **ortho scan** CLI command
   - Discover all modules in a Python project
   - Extract all symbols, call graphs, imports
   - Store in SQLite with:
     - File metadata (path, hash, git commit)
     - Symbol registry (function/class definitions + line numbers)
     - Call graph edges (caller → callee + confidence)
     - Import graph edges (file → file imports)

3. **Real-Repo Testing** (NEW — verifies bugs found in real code)
   - Scan fastapi repository
   - Property-based tests: generate random subsets of fastapi codebase, verify call graph consistency
   - Real-repo scan test: Compare extracted symbols against known fastapi structure

4. **Property-Based Testing** (NEW — catches edge cases)
   - Use hypothesis to generate test inputs (file structures, import patterns, call chains)
   - Each property test runs ≥10 cases automatically
   - Verifies invariants (e.g., "call graph is acyclic", "import graph has no dangling references")

---

## What This Task Does NOT Cover (Out of Scope)

- ❌ Performance optimization (only if scan time >5min for fastapi)
- ❌ Distributed scanning or parallelization
- ❌ Watch mode (`--watch` flag, deferred to Week 6)
- ❌ TypeScript language adapter
- ❌ Changes to shared types (expand only, no breaking changes)
- ❌ Test design (separate: TEST-DESIGNER)
- ❌ Verification running (separate: VERIFIER)

---

## Input Specification

### Source of Truth
- FRD Section 6.3 (Incremental Indexing)
- FRD Section 6.4 (ortho scan contract)
- Existing implementation: `packages/repo-intelligence/src/`
- Real codebase: `C:\Users\urbra\OneDrive\Desktop\Projects\ortho\Repos\fastapi`

### What Already Works
- CallGraphBuilder, ImportGraphBuilder, ModuleDetector, SymbolExtractor (task-006 complete)
- SQLite storage layer (task-001 complete)
- OrthoConfig + .ortho/ directory (task-001 complete)
- Tree-sitter AST parsing

### What Needs Implementation
- **IncrementalIndexer:** 0% complete (stub only)
- **ortho scan command:** 0% complete (CLI skeleton exists)
- **Real-repo integration:** 0% complete
- **Property-based tests:** 0% complete

---

## Output Specification

### Production Code

**File: `packages/repo-intelligence/src/incremental_indexer.py`**

```python
class IncrementalIndexer:
    """
    Incrementally re-index changed files based on git diff.
    
    Public API:
    - index_changes(repo_path: Path, db_path: Path) -> IndexingResult
    """
    
    def index_changes(
        self,
        repo_path: Path,
        db_path: Path
    ) -> IndexingResult:
        """
        Detect changed files since last indexing and re-index only those files.
        
        Returns:
            IndexingResult with:
            - files_changed: int (number of files detected as changed)
            - files_indexed: int (number of files re-indexed)
            - symbols_added: int
            - symbols_removed: int
            - duration_sec: float
        
        Handles:
        - First-time indexing (no git history) — scan all files
        - Subsequent indexing (git diff) — scan changed files only
        - Deleted files — remove from registry
        - Moved/renamed files — detect and update paths
        - Syntax errors in changed files — log and skip gracefully
        """
```

**File: `packages/repo-intelligence/src/cli.py` (update existing)**

Add `ortho scan` command:

```python
@click.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--incremental', is_flag=True, help='Use incremental indexing (git diff based)')
@click.option('--output', type=click.Path(), help='Output .ortho/ directory')
def scan(repo_path: str, incremental: bool, output: str) -> None:
    """
    Scan a Python repository and index all modules, symbols, and call graphs.
    
    Usage:
        ortho scan /path/to/repo
        ortho scan /path/to/repo --incremental
        ortho scan /path/to/repo --output /custom/.ortho
    """
```

---

## Acceptance Criteria (AC)

### AC1: IncrementalIndexer Functionality
**Test coverage:** 12+ tests

- `test_first_time_indexing` — scans all files when no history
- `test_detect_changed_files` — git diff detects modified files
- `test_skip_unchanged_files` — unchanged files not re-indexed
- `test_detect_deleted_files` — deleted files removed from registry
- `test_detect_moved_files` — moved files updated in registry
- `test_preserve_unchanged_symbols` — symbols from unchanged files kept
- `test_update_affected_dependencies` — if A.py changes and B.py imports A, re-index B
- `test_syntax_error_handling` — graceful error on syntax errors in changed file
- `test_result_metrics` — IndexingResult has all required fields
- `test_empty_diff_no_changes` — no files changed → IndexingResult reports 0
- `test_first_commit_no_git_history` — handles repos with single commit
- `test_incremental_performance` — re-indexes faster than full scan

**Verdict:** All 12 tests PASS (EXIT 0), no xfail needed

---

### AC2: ortho scan Command
**Test coverage:** 8+ tests

- `test_scan_command_exists` — `ortho scan` CLI command callable
- `test_scan_creates_ortho_directory` — `.ortho/` created on first run
- `test_scan_populates_symbol_registry` — symbols stored in SQLite
- `test_scan_populates_call_graph` — call edges stored
- `test_scan_populates_import_graph` — import edges stored
- `test_scan_creates_metadata` — file metadata (path, hash, commit) stored
- `test_scan_incremental_flag` — `--incremental` flag accepted and used
- `test_scan_output_flag` — `--output /custom/.ortho` flag creates custom directory

**Verdict:** All 8 tests PASS (EXIT 0), no xfail needed

---

### AC3: Real-Repo Scan Verification (NEW)
**Test coverage:** 1 property-based test + 1 real-repo scan test

- `test_scan_fastapi_real_repo` — **Real-repo test:** 
  - Scan `C:\Users\urbra\OneDrive\Desktop\Projects\ortho\Repos\fastapi`
  - Verify ≥500 symbols extracted (classes, functions)
  - Verify ≥200 call edges found
  - Verify ≥50 import edges found
  - Verify no crashes on real codebase

- `test_call_graph_invariant_property` — **Property test:**
  - Generate random subsets of Python files
  - Verify call graph property: **no cycles** (call graph is acyclic)
  - Verify invariant: every callee in call graph exists as symbol
  - Use hypothesis with ≥10 generated cases

**Verdict:** Property test PASSES with ≥10 cases, real-repo test PASSES with ≥500 symbols extracted

---

### AC4: Zero Regressions
**Regression verification:**

1. `pytest packages/repo-intelligence/tests/ -v --tb=short`  
   Expected: All previously passing tests continue to pass (task-006 baseline maintained)

2. `pytest -v --tb=short` (all packages)  
   Expected: No new test failures in any package

---

## Interface Contracts

All methods return stable types:

```python
# Input
Path    # pathlib.Path

# Output
IndexingResult:
    files_changed: int
    files_indexed: int
    symbols_added: int
    symbols_removed: int
    duration_sec: float

ScanResult:
    symbols_count: int
    call_edges_count: int
    import_edges_count: int
    duration_sec: float
```

---

## Data Flow

```
Python repository (real codebase)
    ↓
git diff (detect changed files)
    ↓
IncrementalIndexer.index_changes() → IndexingResult
    ↓
CallGraphBuilder, ImportGraphBuilder, ModuleDetector, SymbolExtractor
    ↓
SQLite storage (with git metadata: commit hash, timestamp)
    ↓
ortho scan command output
```

---

## Test Strategy (NEW: Property-Based + Real-Repo)

### Traditional Unit Tests (≥8 tests)
- ortho scan command exists and runs
- incremental indexing detects changes correctly
- regression tests (task-006 baseline maintained)

### Property-Based Tests (≥1, uses hypothesis)
- **Test:** `test_call_graph_invariant_property`
- **Property:** Call graph has no cycles (acyclic)
- **Generated inputs:** Random file structures, random call chains
- **Cases:** hypothesis generates ≥10 test cases automatically
- **Failure:** If property violated, hypothesis shrinks to minimal failing case

### Real-Repo Scan Test (≥1, uses actual fastapi codebase)
- **Test:** `test_scan_fastapi_real_repo`
- **Input:** `C:\Users\urbra\OneDrive\Desktop\Projects\ortho\Repos\fastapi`
- **Assertions:**
  - ≥500 symbols extracted (not mocks, real fastapi classes/functions)
  - ≥200 call edges found
  - ≥50 import edges found
  - No crashes, no unhandled exceptions
- **Purpose:** Verify tool works on real code, catches edge cases hypothesis might miss

---

## Expected Test Metrics

- **Unit tests:** 12+ (AC1 incremental indexing, AC2 scan command)
- **Property tests:** 1+ (AC3 call graph invariant)
- **Real-repo tests:** 1+ (AC3 fastapi scan)
- **Regression tests:** ≥30 (from task-006 baseline)
- **Total:** 45+ tests
- **Expected coverage:** ≥80%
- **Expected pass rate:** 100% (no failures, property tests run ≥10 cases each)

---

## Known Limitations & Deferrals

All acceptance criteria (AC1–AC4) are within scope and must be implemented.

If the BUILDER discovers legitimate limitations:
1. Document immediately in implementation-notes.md
2. Mark affected tests with `@pytest.mark.xfail(reason="documented limitation")`
3. Report to human at GATE 3 for approval

---

## Definition of Done

1. ✓ All acceptance criteria (AC1–AC4) implemented and verified via pytest
2. ✓ All tests execute via pytest (real pytest output, not designs)
3. ✓ Property-based tests run ≥10 cases each (hypothesis evidence)
4. ✓ Real-repo scan verifies ≥500 symbols in fastapi (not mocks)
5. ✓ No regressions in other test suites
6. ✓ implementation-notes.md documents what was built
7. ✓ VERIFIER runs pilot tests + full suite + real-repo scan
8. ✓ REVIEWER approves code quality and behavior
9. ✓ Merged to main with evidence reference

---

*Created by PLANNER*  
*Status: DRAFT → awaiting human approval at GATE 1*
