# Task-003 Spec: Call Graph + Incremental Indexing

**Status:** DRAFT → APPROVED (awaiting GATE 1)  
**Workflow:** `.ases/workflows/feature.md`

---

## Objective

Extend `repo-intelligence` package with:
1. Static call graph analysis (pyan3)
2. Dependency extraction (requirements.txt, pyproject.toml)
3. Module/package detection
4. Incremental re-indexing (git diff based)
5. CLI command: `ortho index` with `--watch` mode

Output: Python repos now have complete function call graphs and live incremental indexing.

---

## Exact Files to Create

```
shared/types/src/
  ├── call-graph.ts          (NEW: CallGraphBuilder interface + CallEdge type)
  ├── dependency-graph.ts    (NEW: DependencyGraph + DependencyEdge types)
  └── module.ts              (NEW: Module interface)

packages/repo-intelligence/src/
  ├── call_graph.py          (NEW: pyan3 integration, call edge extraction)
  ├── dependency_graph.py    (NEW: requirements.txt + pyproject.toml parser)
  ├── module_detector.py     (NEW: detect packages and namespace packages)
  ├── incremental_indexer.py (NEW: git diff based re-indexer)
  └── __init__.py            (MODIFY: export new classes)

apps/cli/src/commands/
  └── index.ts               (NEW: ortho index command with --watch)

apps/cli/src/
  └── cli.ts                 (MODIFY: register index command)
```

**Files NOT to touch:**
- `shared/storage/` — no schema changes (use existing tables)
- `shared/types/src/adapter.ts` — language adapters stable
- `packages/repo-intelligence/src/symbol_registry.py` — reuse as-is
- `packages/repo-intelligence/src/import_graph.py` — reuse as-is

---

## Input/Output Contracts

### CallGraphBuilder (call_graph.py)

```python
class CallGraphBuilder:
    def __init__(self, repo_root: Path, python_files: List[Path]):
        """repo_root: project root, python_files: paths to .py files"""
    
    def build_call_graph(self) -> List[CallEdge]:
        """
        Returns: list of CallEdge objects
        CallEdge = (caller_id, callee_id, call_site_line, confidence)
        confidence: 1.0 = definite call, 0.8 = recursive/dynamic, 0.6 = module call
        Raises: CallGraphError (file not readable, pyan3 failure)
        """
```

**Input:** List of Python file paths, repo_root  
**Output:** `List[CallEdge]` where:
- caller_id: Symbol.id (function/method making the call)
- callee_id: Symbol.id (function/method being called)
- call_site_line: line number of the call
- confidence: 0.6 - 1.0 (lower for uncertain dynamic calls)

**Behavior:**
- Extract calls from AST (avoid regex hacks)
- Handle async/await (`await foo()`)
- Handle walrus (`:=`)
- Handle match statements (3.10+)
- Recursive calls have confidence 0.8
- Circular calls detected and confidence 0.8
- External calls (outside repo) skipped
- Built-in calls (print, len, etc.) skipped

---

### DependencyGraphBuilder (dependency_graph.py)

```python
class DependencyGraphBuilder:
    def __init__(self, repo_root: Path):
        """Scans repo_root for requirements.txt and pyproject.toml"""
    
    def build_dependency_graph(self) -> List[DependencyEdge]:
        """
        Returns: list of DependencyEdge objects
        DependencyEdge = (importer_module, package_name, version, is_external)
        """
```

**Input:** repo_root  
**Output:** `List[DependencyEdge]`
- importer_module: "project_root" for top-level project dependencies
- package_name: name of external package (e.g., "pyan3", "gitpython")
- version: version constraint (e.g., ">=3.10", "==1.5.2") or None if unversioned
- is_external: always True for dependencies (no internal deps tracked here)

**Behavior:**
- Parse `requirements.txt` (line by line, skip comments)
- Parse `pyproject.toml` [tool.poetry.dependencies] (poetry only for now)
- Handle PEP 508 version specifiers (==, >=, <=, ~=, !=, @, extras)
- If both exist, merge (pyproject takes precedence if conflict)
- If neither exists, return empty list (no error)
- Skip lines with `#` and empty lines
- Malformed lines logged and skipped (fail-forward)

---

### ModuleDetector (module_detector.py)

```python
class ModuleDetector:
    def __init__(self, repo_root: Path):
        """Scans repo_root for Python packages"""
    
    def detect_modules(self) -> List[Module]:
        """
        Returns: list of Module objects
        Module = (name, root_path, type, file_paths)
        type: "regular" (has __init__.py) | "namespace" (PEP 420)
        """
```

**Input:** repo_root  
**Output:** `List[Module]`
- name: package name (e.g., "myproject.auth", "myproject")
- root_path: path to package directory
- type: "regular" or "namespace"
- file_paths: list of .py files in the package

**Behavior:**
- Scan for `__init__.py` (regular packages)
- Scan for namespace packages (directories with .py files, no `__init__.py`)
- Ignore `__pycache__`, `.pytest_cache`, `.tox`, `venv`, `env`
- Ignore hidden directories (starting with `.`)
- Fast (cache results, invalidate only on file add/delete)
- Handle deeply nested structures (don't limit depth)

---

### IncrementalIndexer (incremental_indexer.py)

```python
class IncrementalIndexer:
    def __init__(self, repo_root: Path, storage: OrthoDatabase):
        """repo_root: project root, storage: database connection"""
    
    def index_incremental(self) -> IndexDelta:
        """
        Compute git diff, re-index only changed files.
        Returns: IndexDelta = (added_symbols, modified_symbols, removed_symbols)
        Raises: NotAGitRepoError if .git not found
        """
```

**Input:** repo_root, database  
**Output:** `IndexDelta` object:
- added_symbols: List[Symbol] new in this index
- modified_symbols: List[Symbol] changed since last index
- removed_symbols: List[Symbol] deleted since last index

**Behavior:**
- Check if repo_root is a git repo (look for .git/)
- If not a git repo, treat all files as "modified" (full re-index)
- Compute git diff: `git diff --name-status <last_indexed_at>...HEAD`
- Added files (A): extract symbols, calls, imports
- Modified files (M): clear old entries, extract new ones
- Deleted files (D): remove from registry
- Merge results into Symbol registry, CallEdge table, ImportEdge table
- Update last_indexed_at timestamp in database
- Fast: < 5 seconds for 50-file change

**Edge Cases:**
- First run: last_indexed_at is None, treat all files as "modified"
- Dirty working tree: git diff uses HEAD (ignores unstaged changes)
- Detached HEAD: still works (diff from HEAD)
- Submodules: only index main repo (ignore submodules)

---

### `ortho index` CLI Command

```typescript
// apps/cli/src/commands/index.ts

interface IndexCommand {
  name: "index"
  description: "Index Python repo for call graphs and dependencies"
  options: {
    watch?: boolean  // --watch: enable watch mode (incremental re-index)
    verbose?: boolean // --verbose: show per-file progress
  }
}

// Usage:
// $ ortho index                   # Full re-index
// $ ortho index --watch           # Watch mode (Ctrl+C to exit)
// $ ortho index --watch --verbose # Verbose watch mode
```

**Behavior:**
- Read config from `.ortho/config.json`
- Find all Python files
- Call CallGraphBuilder, DependencyGraphBuilder, ModuleDetector, SymbolExtractor
- Store results in database
- Output: "Indexed X symbols, Y calls, Z dependencies"
- Watch mode:
  - Polls git diff every 2 seconds
  - On change: incremental re-index
  - Output per-file progress (if --verbose)
  - Handle Ctrl+C gracefully (close database, exit 0)
- Errors: graceful (skip unreadable files, log, continue)

**Examples:**
```bash
$ ortho index
Indexed 1,245 symbols, 3,891 calls, 18 dependencies

$ ortho index --watch
Watching for changes... (Ctrl+C to exit)
[Modified] src/auth/service.py: +12 calls, +3 symbols
[Modified] src/utils/validators.py: +2 calls
Indexed 1,247 symbols, 3,905 calls, 18 dependencies
...
```

---

## Acceptance Criteria (Binary, Testable)

1. **Call graph builder extracts calls from Python AST** — No regex parsing, uses AST only
2. **Handles Python 3.10+ syntax** — Walrus (:=), match, async/await work correctly
3. **Dependency graph parses requirements.txt** — Can read file, extract packages + versions
4. **Dependency graph parses pyproject.toml** — Handles [tool.poetry.dependencies]
5. **Module detector finds regular packages** — Identifies __init__.py directories
6. **Module detector finds namespace packages** — PEP 420 packages detected (no __init__.py)
7. **Incremental indexer computes git diff** — Uses git diff to find changed files
8. **Incremental indexer re-indexes only changed files** — Skips unchanged files (measurable time difference)
9. **ortho index command runs without error** — Exit code 0, produces output
10. **ortho index --watch responds to file changes** — Detects and re-indexes within 3 seconds
11. **ortho index --watch handles Ctrl+C** — Graceful shutdown, exit code 0
12. **All file I/O handles missing files gracefully** — No crashes on permission denied
13. **Performance: full index < 30s** — Typical 1000-file repo indexed in < 30s
14. **Performance: incremental re-index < 5s** — 50-file change re-indexed in < 5s
15. **Call graph confidence scores assigned** — 0.6 - 1.0, lower for dynamic/recursive calls

---

## Data Flow

```
ortho index
  ↓
  1. Find all .py files (from PythonAdapter)
  2. Extract symbols (from SymbolExtractor, task-002)
  3. Build call graph (CallGraphBuilder) → store CallEdge
  4. Build dependency graph (DependencyGraphBuilder) → store DependencyEdge
  5. Detect modules (ModuleDetector) → internal tracking (not stored)
  6. Update database
  ↓ output
  "Indexed X symbols, Y calls, Z dependencies"

ortho index --watch
  ↓
  1. Run full index (above)
  2. Poll git diff every 2 seconds
  3. On change detected:
     ↓
     IncrementalIndexer.index_incremental()
     - Compute diff (added/modified/deleted)
     - Re-index changed files only
     - Update database
     ↓ output
     "[Modified] file.py: +N calls, +M symbols"
  4. On Ctrl+C: close database, exit 0
```

---

## Storage / Database

**No new tables required.** Reuse existing:
- `symbols` (from task-002)
- `call_edges` (new records: CallEdge rows)
- `import_edges` (from task-002)
- `repositories` (add `last_indexed_at` column if missing)

---

## Dependencies (External)

From FRD Section 13:
- `pyan3` (Python call graph) — already listed in pyproject.toml
- `gitpython` (git integration) — already listed
- `toml` or `tomli` (TOML parsing) — check if already present, add if needed

No new dependencies without explicit ARCHITECT approval.

---

## Rollback Triggers

- [ ] Build fails (compilation error)
- [ ] > 3 test failures
- [ ] Call graph confidence drops below 0.5 for > 50% of calls
- [ ] Incremental indexer misses > 10% of changed files
- [ ] Watch mode CPU usage > 20% on idle
- [ ] Git integration fails (not a repo)

---

## Testing Strategy (for TEST-DESIGNER)

1. **Unit tests** (per module):
   - CallGraphBuilder: extract calls from simple functions, async, walrus, match, recursion
   - DependencyGraphBuilder: parse requirements.txt, pyproject.toml, mixed
   - ModuleDetector: find regular packages, namespace packages, deeply nested
   - IncrementalIndexer: compute diff, re-index subset, handle edge cases

2. **Integration tests:**
   - End-to-end: `ortho index` on test repo, verify output
   - Incremental: modify file, run `ortho index --watch`, verify only changed file re-indexed
   - Watch mode: simulate file changes, verify detection < 3s

3. **Edge cases:**
   - Empty repo (no Python files)
   - Repo without .git (not a git repo)
   - Malformed requirements.txt, pyproject.toml
   - Circular calls, recursive calls
   - Very large call graphs (1000+ calls)
   - Permission denied on file read (skip gracefully)

4. **Regression:**
   - Existing symbol extraction still works
   - Existing import graph still works
   - No new dependencies break existing tests

---

*End of spec.md. PLANNER ready for ARCHITECT review after GATE 1 approval.*
