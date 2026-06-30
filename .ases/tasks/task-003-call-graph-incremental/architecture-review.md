# Task-003 Architecture Review

**Status:** APPROVED (GATE 2)  
**Reviewer:** ARCHITECT  
**Date:** 2026-06-30  
**Workflow:** `.ases/workflows/feature.md`

---

## Overview

Reviewed spec.md and plan.md for task-003 (Call Graph + Incremental Indexing). Architecture is sound. No new ADRs required (all decisions already covered by ADR-004, ADR-005). Ready for BUILDER.

---

## Module Boundaries

### New Modules

**`packages/repo-intelligence/call_graph.py`**
- Responsibility: Extract call edges from Python AST (pyan3)
- Dependency: PythonAdapter (task-002), Symbol type (shared/types)
- Public API: `CallGraphBuilder.build_call_graph() → List[CallEdge]`
- No circular dependencies: ✓ (only depends on shared types + pyan3)

**`packages/repo-intelligence/dependency_graph.py`**
- Responsibility: Parse requirements.txt + pyproject.toml
- Dependency: Path utilities, toml library
- Public API: `DependencyGraphBuilder.build_dependency_graph() → List[DependencyEdge]`
- No circular dependencies: ✓

**`packages/repo-intelligence/module_detector.py`**
- Responsibility: Detect Python packages (regular + namespace)
- Dependency: Path utilities, shared/types
- Public API: `ModuleDetector.detect_modules() → List[Module]`
- No circular dependencies: ✓

**`packages/repo-intelligence/incremental_indexer.py`**
- Responsibility: Compute git diff, re-index only changed files
- Dependency: git (GitPython), SymbolExtractor, CallGraphBuilder, DependencyGraphBuilder, storage
- Public API: `IncrementalIndexer.index_incremental() → IndexDelta`
- No circular dependencies: ✓ (depends on other analyzers, but they don't depend back)

**`apps/cli/src/commands/index.ts`**
- Responsibility: CLI entrypoint for `ortho index` command
- Dependency: repo-intelligence package (Python), database
- Public API: `ortho index [--watch] [--verbose]`
- No circular dependencies: ✓

### TypeScript Type Definitions (shared/types)

**`call-graph.ts`**
- Types: `CallEdge`, `CallGraphBuilder` interface
- Used by: repo-intelligence (Python), CLI (TypeScript)
- No circular dependencies: ✓

**`dependency-graph.ts`**
- Types: `DependencyEdge`, `DependencyGraph` interface
- Used by: repo-intelligence (Python), context-hub (Phase 2)
- No circular dependencies: ✓

**`module.ts`**
- Types: `Module` interface
- Used by: repo-intelligence (Python), architecture-intelligence (Phase 2)
- No circular dependencies: ✓

---

## Data Flow

### Full Index Flow

```
ortho index
  │
  ├─→ Load config from .ortho/config.json
  │
  ├─→ Find all .py files (from PythonAdapter, task-002)
  │
  ├─→ SymbolExtractor.extract_symbols() (task-002, reuse)
  │     └─→ Store in DB: symbols table
  │
  ├─→ CallGraphBuilder.build_call_graph()
  │     └─→ Parse AST (pyan3), extract edges
  │     └─→ Store in DB: call_edges table
  │
  ├─→ DependencyGraphBuilder.build_dependency_graph()
  │     └─→ Parse requirements.txt + pyproject.toml
  │     └─→ Store in DB: dependency_edges table
  │
  ├─→ ModuleDetector.detect_modules()
  │     └─→ Detect __init__.py + namespace packages
  │     └─→ Store in memory (not DB, internal only)
  │
  └─→ Output: "Indexed X symbols, Y calls, Z dependencies"
```

### Incremental Index Flow

```
ortho index --watch
  │
  ├─→ Run full index (above)
  │
  └─→ Loop:
       │
       ├─→ Poll git diff every 2s
       │
       ├─→ If changes detected:
       │   │
       │   ├─→ IncrementalIndexer.index_incremental()
       │   │     │
       │   │     ├─→ Compute git diff (added/modified/deleted)
       │   │     │
       │   │     ├─→ For added files: extract symbols, calls, deps
       │   │     ├─→ For modified files: clear old entries, extract new
       │   │     ├─→ For deleted files: remove entries
       │   │     │
       │   │     └─→ Update DB + return IndexDelta
       │   │
       │   └─→ Output: "[Modified] file.py: +N calls, +M symbols"
       │
       └─→ On Ctrl+C: close DB, exit 0
```

### Database Schema (No Changes)

Reuse existing tables from task-001:
- `symbols` — Symbol records (existing)
- `call_edges` — **New rows:** CallEdge records (new table or new records in existing)
- `import_edges` — ImportEdge records (existing)
- `repositories` — Add `last_indexed_at` column (if not present)

**No breaking schema changes.** All new data fits into existing structure.

---

## API Contracts

### CallGraphBuilder

```python
class CallGraphBuilder:
    def __init__(self, repo_root: Path, python_files: List[Path]) -> None:
        """
        Args:
            repo_root: Path to project root
            python_files: List of .py file paths (absolute or relative to repo_root)
        """
    
    def build_call_graph(self) -> List[CallEdge]:
        """
        Extract function/method calls from Python AST.
        
        Returns:
            List[CallEdge]: caller_id, callee_id, call_site_line, confidence
        
        Raises:
            FileNotFoundError: If python_files don't exist
            CallGraphError: If pyan3 fails (e.g., syntax error in source)
        
        Confidence scores:
            - 1.0: Definite call (static analysis certain)
            - 0.8: Recursive or circular call (certain but recursive)
            - 0.6: Module call (obj.method where obj type uncertain)
        """
```

**Contract:** Caller IDs and callee IDs MUST match Symbol.id from SymbolExtractor (task-002). If not found, skip edge (don't create orphan edges).

---

### DependencyGraphBuilder

```python
class DependencyGraphBuilder:
    def __init__(self, repo_root: Path) -> None:
        """
        Args:
            repo_root: Path to project root
        """
    
    def build_dependency_graph(self) -> List[DependencyEdge]:
        """
        Parse requirements.txt and/or pyproject.toml for dependencies.
        
        Returns:
            List[DependencyEdge]: (importer_module, package_name, version, is_external)
        
        Behavior:
            - Returns empty list if no requirements.txt or pyproject.toml
            - Skips malformed lines (fail-forward, log warning)
            - Merges requirements.txt + pyproject.toml (pyproject precedence)
        """
```

**Contract:** Requires PEP 508 compliance for version specifiers. External packages only (no internal module dependencies tracked here).

---

### ModuleDetector

```python
class ModuleDetector:
    def __init__(self, repo_root: Path) -> None:
        """
        Args:
            repo_root: Path to project root
        """
    
    def detect_modules(self) -> List[Module]:
        """
        Detect Python packages (regular and namespace).
        
        Returns:
            List[Module]: name, root_path, type, file_paths
        
        Behavior:
            - Regular packages: directories with __init__.py
            - Namespace packages: PEP 420 (no __init__.py)
            - Ignores: __pycache__, .pytest_cache, venv, env, hidden dirs
        """
```

**Contract:** Module names must be fully qualified (e.g., "myproject.auth.service"). Root path must be absolute.

---

### IncrementalIndexer

```python
class IncrementalIndexer:
    def __init__(self, repo_root: Path, storage: OrthoDatabase) -> None:
        """
        Args:
            repo_root: Path to project root
            storage: OrthoDatabase instance (connected)
        """
    
    def index_incremental(self) -> IndexDelta:
        """
        Compute git diff and re-index only changed files.
        
        Returns:
            IndexDelta: (added_symbols, modified_symbols, removed_symbols)
        
        Behavior:
            - If not a git repo: treat all files as modified (full re-index)
            - Computes diff since last_indexed_at timestamp
            - Re-indexes added/modified files only
            - Deletes entries for removed files
            - Updates last_indexed_at timestamp
        
        Raises:
            NotAGitRepoError: If .git doesn't exist and strict=True
        """
```

**Contract:** Must be idempotent (running twice with same input produces same result). Diff is computed from git, not file system.

---

### `ortho index` CLI

```typescript
interface IndexCommand {
  command: "index"
  options: {
    watch?: boolean      // Enable watch mode (incremental re-index)
    verbose?: boolean    // Show per-file progress
  }
}

// Exit codes:
// 0: Success (index complete or watch exited via Ctrl+C)
// 1: Error (build failed, DB error, not a git repo, etc.)
```

**Contract:** Command must handle Ctrl+C gracefully (close DB, exit 0). Database must not be left in locked state.

---

## Dependency Analysis

### External Dependencies (No New)

All dependencies listed in FRD Section 13:
- ✅ `pyan3` — Call graph extraction (already in pyproject.toml)
- ✅ `gitpython` — Git integration (already in pyproject.toml)
- ✅ `toml` or `tomli` — TOML parsing (check if present, add if needed)

**No new dependencies added.** If `toml` missing, BUILDER adds it to pyproject.toml (already approved in FRD).

### Internal Dependencies

```
CallGraphBuilder
  ├─→ pyan3 (external)
  ├─→ shared/types (CallEdge)
  └─→ Symbol (from SymbolExtractor, task-002)

DependencyGraphBuilder
  ├─→ toml (external)
  └─→ shared/types (DependencyEdge)

ModuleDetector
  ├─→ Path utilities (stdlib)
  └─→ shared/types (Module)

IncrementalIndexer
  ├─→ gitpython (external)
  ├─→ CallGraphBuilder
  ├─→ DependencyGraphBuilder
  ├─→ SymbolExtractor (task-002)
  ├─→ ImportGraphBuilder (task-002)
  └─→ OrthoDatabase (shared/storage)

CLI Command
  ├─→ IncrementalIndexer
  ├─→ OrthoDatabase
  └─→ OrthoConfig
```

**No circular dependencies detected.** IncrementalIndexer depends on other builders, but they don't depend back on it.

---

## Design Decisions

### 1. Why pyan3 for call graphs?

**Decision:** Use pyan3 (static call graph generator).

**Rationale:**
- FRD Section 13, Repo 4: pyan3 specified and approved
- Lightweight (no external servers needed)
- Fast (< 100ms for typical files)
- Handles Python 3.10–3.14 (modern syntax)
- Local-first (Principle 6)

**Alternative rejected:** AST-only parsing (reinventing pyan3) — too much work, pyan3 already optimized.

---

### 2. Why git diff for incremental indexing?

**Decision:** Use git diff to compute changed files, re-index only those.

**Rationale:**
- Fast (git diff is O(n) in file count, not O(n²))
- Accurate (git is source of truth for changes)
- Local-first (no external service)
- Stateless (can resume from any commit)

**Alternative rejected:** File system watches (too noisy, OS-specific, race conditions).

---

### 3. Why separate modules for CallGraphBuilder, DependencyGraphBuilder, ModuleDetector?

**Decision:** Three separate classes, each with single responsibility.

**Rationale:**
- Principle 5: "Small composable modules"
- Principle 8: "Every capability independently usable"
- Test independently (each class has its own test suite)
- Reuse independently (e.g., DependencyGraphBuilder can be used without CallGraphBuilder)
- Evolve independently (e.g., upgrade pyan3 without affecting dependency parser)

**Alternative rejected:** One "IndexBuilder" class doing all three (too many responsibilities, hard to test, hard to reuse).

---

### 4. Why confidence scores in CallEdge?

**Decision:** Include confidence (0.6–1.0) in each CallEdge.

**Rationale:**
- Static analysis is probabilistic (not all calls are certain)
- Recursive/circular calls have lower confidence
- Phase 2 (Arch Intelligence) uses confidence for impact analysis
- Enables filtering in retrieval (high confidence calls = strong coupling)

**Limitation:** Confidence scores are heuristics, not guarantees. Documented in Phase 2 usage.

---

### 5. Why poll every 2 seconds in watch mode?

**Decision:** Poll git diff every 2 seconds.

**Rationale:**
- Balance responsiveness (detect changes within 2–3 seconds)
- Avoid CPU spike (polling too fast burns CPU)
- Still reasonable for developer workflow (git commits every 10–30s on average)
- User can press Ctrl+C anytime

**Tradeoff:** Not real-time (would require file system events via `watchdog` library, adds dependency).

---

### 6. Why no schema changes?

**Decision:** Reuse existing database schema (no new tables).

**Rationale:**
- CallEdge, DependencyEdge, Module fit into existing table structure
- Reduces migration complexity
- Backward compatible (task-002 data untouched)
- Storage layer (task-001) already supports arbitrary edge types

**Caveat:** May need to add `last_indexed_at` column to `repositories` table (check during BUILDER phase).

---

## Risk Assessment

| Risk | Severity | Mitigation | Residual |
|------|----------|-----------|----------|
| pyan3 misses dynamic calls | MEDIUM | Confidence scores flag uncertain edges; document in Phase 2 usage | ACCEPTED |
| Git integration fails (not a git repo) | MEDIUM | Graceful fallback: treat all files as modified, full re-index | ACCEPTED |
| Watch mode CPU spike | LOW | Debounce 2s, sleep between polls | ACCEPTED |
| Malformed requirements.txt breaks parser | LOW | Fail-forward: skip malformed lines, log warning, continue | ACCEPTED |
| Module detection slow on deep nesting | LOW | Cache results, invalidate only on file add/delete | ACCEPTED |

No blockers. All risks mitigated or acceptable.

---

## Extension Points (for Phase 2+)

1. **Language support:** Currently Python only. Phase 2 adds TypeScript (new adapters per language).
2. **Call graph visualization:** Phase 2 (Arch Intelligence) visualizes call graphs.
3. **Dependency scanning:** Phase 2+ can extend DependencyGraphBuilder to check for vulnerabilities.
4. **Real-time watch:** Phase 3+ can replace polling with file system events (`watchdog` library).
5. **Incremental symbol extraction:** Phase 3+ can optimize SymbolExtractor to only re-extract changed files (currently re-extracts all).

All extension points are backward compatible. No API changes needed.

---

## Definition of Done (ARCHITECT)

- ✅ Module boundaries are clear and coherent
- ✅ No circular dependencies detected
- ✅ All new APIs defined with input/output contracts
- ✅ Data flow is clear (no validation confusion)
- ✅ Security/scalability/extensibility risks identified and mitigated
- ✅ No new ADRs required (all covered by existing ADRs)
- ✅ Verdict: **APPROVED**

---

## Verdict

**APPROVED ✓**

Task-003 architecture is sound. No design issues. All modules have single responsibility. No circular dependencies. APIs are clear. Data flow is well-defined. Ready for BUILDER to implement.

**Next step:** BUILDER implements 5 atomic tasks in order (see plan.md).

---

*ARCHITECT session complete. GATE 2 ready for human approval.*
