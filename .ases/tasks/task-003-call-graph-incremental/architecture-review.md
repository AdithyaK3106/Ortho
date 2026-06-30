# Task-003 Architecture Review

**Status:** APPROVED (GATE 2)  
**Reviewer:** ARCHITECT  
**Date:** 2026-06-30  
**Workflow:** `.ases/workflows/feature.md`

---

## Overview

Reviewed spec.md and plan.md for task-003 (Call Graph + Incremental Indexing). Architecture is sound. All design decisions align with FRD Principles 5, 6, 8 (small composable modules, local-first, independent capabilities). Ready for BUILDER.

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

### Watch Mode Flow

Watch mode (--watch flag) runs the full index once, then repeatedly:
1. Polls git for changes
2. On changes detected: invokes IncrementalIndexer
3. IncrementalIndexer computes git diff, re-indexes changed files, updates database
4. Continues looping until user interrupts (Ctrl+C)

### Database Schema (Schema Extension)

Call graph data is stored in a new `call_edges` table:

| Column | Type | Notes |
|--------|------|-------|
| caller_id | TEXT | Foreign key to Symbol.id |
| callee_id | TEXT | Foreign key to Symbol.id |
| call_site_line | INTEGER | Line number in source |
| confidence | FLOAT | 0.6–1.0 |

Dependency data is stored in a new `dependency_edges` table:

| Column | Type | Notes |
|--------|------|-------|
| repo_id | TEXT | Foreign key to Repository.id |
| package_name | TEXT | External package name |
| version | TEXT | Version constraint (nullable) |

The `repositories` table requires a new `last_indexed_at` column (TIMESTAMP, nullable) to track incremental index state.

**Schema compatibility:** These tables and columns are additive (no modification or deletion of existing schema). Backward compatible with task-002 data.

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

**Constraint:** Caller IDs and callee IDs must map to Symbol.id from task-002's SymbolExtractor. Orphan edges (where caller or callee Symbol.id does not exist) are invalid.

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
        Parse requirements.txt and pyproject.toml for external dependencies.
        
        Returns:
            List[DependencyEdge]: package_name, version, external flag
        """
```

**Constraint:** Dependency graph covers external packages only. Internal module dependencies are out of scope. Parses two manifest formats: requirements.txt (line-based) and pyproject.toml ([tool.poetry.dependencies] section). Returns empty list if both missing.

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
        Detect Python packages and namespace packages.
        
        Returns:
            List[Module]: name, root_path, type (regular | namespace), file_paths
        """
```

**Contract:** Regular packages have __init__.py. Namespace packages (PEP 420) have no __init__.py. Module names must be fully qualified. Root paths must be absolute.

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
        
        Raises:
            NotAGitRepoError: If .git does not exist or git fails
        
        Behavior:
            - Requires .git directory (repo must be a git repository)
            - Computes git diff since last_indexed_at timestamp
            - Re-indexes added/modified files only
            - Deletes entries for removed files
            - Updates last_indexed_at timestamp in database
        """
```

**Contract:** Requires git repository. Must be idempotent (running twice with same input produces same result). Diff is computed from git, not file system.

---

### `ortho index` CLI

```typescript
interface IndexCommand {
  command: "index"
  options: {
    watch?: boolean      // Enable watch mode
    verbose?: boolean    // Enable per-file progress output
  }
}

// Exit codes:
// 0: Success (index complete, or watch mode exited via Ctrl+C)
// 1: Error (database error, git not a repository, invalid config, etc.)
```

**Contract:** Command orchestrates CallGraphBuilder, DependencyGraphBuilder, ModuleDetector, and (in watch mode) IncrementalIndexer. Database connection is managed by command; resources are released on exit.

---

## Dependency Analysis

### External Dependencies

Required for task-003 implementation:
- `pyan3` — Static Python call graph analysis (specified in FRD Section 13, Repo 4)
- `gitpython` — Git integration (specified in FRD Section 13, Repo 3)
- TOML parser (`toml` or `tomli`) — Parse pyproject.toml (specified in FRD Section 13)

All three are approved in FRD and presumed available in environment. Architecture does not introduce new external dependencies.

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

## Architectural Reasoning

### Module Separation and Composition

Four independent analyzers are composed by IncrementalIndexer and the CLI command:
- CallGraphBuilder: extracts call relationships
- DependencyGraphBuilder: extracts package dependencies
- ModuleDetector: identifies package structure
- Each is independently testable and reusable

This separation aligns with FRD Principles 5 ("Small composable modules") and 8 ("Every capability independently usable"). Modules do not depend on each other; IncrementalIndexer composes them.

### Call Graph Analysis via AST

CallGraphBuilder parses Python source through abstract syntax tree (AST) to identify function/method invocations. Caller and callee are identified by Symbol.id from task-002's SymbolExtractor. Each call edge carries a confidence score (0.6–1.0) to indicate certainty, as static analysis cannot guarantee all dynamic calls.

### Dependency Extraction

DependencyGraphBuilder parses two explicit manifests: requirements.txt (line-by-line) and pyproject.toml (TOML format). This architecture assumes these files are authoritative; it does not infer dependencies from imports. Missing files result in empty output.

### Incremental Re-indexing via Git

IncrementalIndexer requires a git repository. It computes the git diff since the last indexed state (tracked in `repositories.last_indexed_at`). Only changed files are re-analyzed. This architecture mandates git as the source of truth for which files changed.

### Storage Schema Extension

Call graph and dependency data are stored in new tables (`call_edges`, `dependency_edges`) with foreign keys to `symbols` and `repositories`. The `repositories` table gains a `last_indexed_at` timestamp column. This is purely additive (no deletion or modification of existing schema).

### CLI Layering

The CLI command `ortho index` orchestrates three phases:
1. Full index: SymbolExtractor → CallGraphBuilder → DependencyGraphBuilder → ModuleDetector
2. Store: Write all results to database
3. Output: Report counts

Watch mode repeats step 2–3 on git changes detected via IncrementalIndexer.

---

## Architectural Risk Assessment

| Risk | Severity | Mitigation | Residual |
|------|----------|-----------|----------|
| Static analysis incomplete (pyan3 misses dynamic calls) | MEDIUM | Confidence scores range 0.6–1.0 to signal certainty. Phase 2 (Arch Intelligence) interprets scores when scoring impact. | ACCEPTED |
| Git repository required but not guaranteed | HIGH | IncrementalIndexer raises NotAGitRepoError if .git missing. CLI must handle and report. | MITIGATED |
| Dependency parsing assumes canonical manifests | MEDIUM | Architecture assumes requirements.txt / pyproject.toml are authoritative. No inference from imports. If manifests missing or incomplete, dependencies missing. | ACCEPTED |
| Schema extension may conflict with concurrent processes | MEDIUM | Database writes occur within single ortho-index process. Phase 3 (Execution) must serialize schema migrations. | ACCEPTED |

No architectural blockers. Git requirement is explicit contract of IncrementalIndexer.

---

## Extensibility

**Python only, currently.** CallGraphBuilder, DependencyGraphBuilder, ModuleDetector all target Python. Supporting additional languages (TypeScript, Go, etc.) requires new adapters and new detector implementations. The architecture does not preclude this; each language adapter can implement its own builders.

**Call edge semantics are stable.** The `CallEdge` type (caller_id, callee_id, call_site_line, confidence) is defined in shared/types and stored in a standard table. Changes to call edge analysis (e.g., improved heuristics for confidence) do not require schema changes.

**Dependency detection is modular.** DependencyGraphBuilder depends only on TOML parsing and file I/O. Extending it to parse other manifests (Pipfile, poetry.lock, setup.py) requires only new code paths within the same builder; no API changes.

---

## Definition of Done (ARCHITECT)

- ✅ Module boundaries are clear and coherent
- ✅ No circular dependencies within repo-intelligence or between packages
- ✅ All new APIs defined with input/output contracts and error handling
- ✅ Data flow is clear (CLI → builders → database → storage)
- ✅ Architectural risks identified (git requirement, static analysis limits, manifest assumptions)
- ✅ Schema is additive and backward compatible
- ✅ Extensibility clear (Python-only now, new languages require new adapters)
- ✅ Verdict: **APPROVED**

---

## Verdict

**APPROVED ✓**

Task-003 architecture is sound. No design issues. All modules have single responsibility. No circular dependencies. APIs are clear. Data flow is well-defined. Ready for BUILDER to implement.

**Next step:** BUILDER implements 5 atomic tasks in order (see plan.md).

---

*ARCHITECT session complete. GATE 2 ready for human approval.*
