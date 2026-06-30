# Task-003 Plan: Call Graph + Incremental Indexing

**Phase:** Phase 1 — Foundation (Week 5–6)  
**Workflow:** `.ases/workflows/feature.md`  
**Status:** DRAFT → PLANNED (awaiting GATE 1 approval)

---

## Feature Summary

Extend repo-intelligence with call graph analysis and incremental indexing. Repo-intelligence can now:
1. Build a static call graph (pyan3) for Python files
2. Extract and store dependency graphs (requirements.txt, pyproject.toml)
3. Detect Python modules and packages
4. Re-index only changed files (git diff based) for fast updates
5. Provide `ortho index --watch` for live tracking

This unlocks cross-function analysis in Phase 2 (impact detection, blast radius).

---

## Atomic Tasks (5 total)

### Task 1: CallGraphBuilder interface + pyan3 integration
**Est.:** 60 min  
**Depends on:** task-002 (PythonAdapter exists)  
**Acceptance:**
- [ ] `CallGraphBuilder` interface defined in `shared/types/src/call-graph.ts`
- [ ] `packages/repo-intelligence/src/call_graph.py` imports pyan3 and extracts call edges
- [ ] Handles Python 3.10–3.14 (walrus, match, async/await)
- [ ] Call edges returned with caller_id, callee_id, call_site_line, confidence
- [ ] Circular calls detected and confidence lowered to 0.8

**Files:** 
- Create: `shared/types/src/call-graph.ts`
- Create: `packages/repo-intelligence/src/call_graph.py`
- Modify: `packages/repo-intelligence/src/__init__.py` (export)

---

### Task 2: DependencyGraphBuilder (requirements + pyproject)
**Est.:** 45 min  
**Depends on:** Task 1 complete  
**Acceptance:**
- [ ] `DependencyGraph` interface defined in `shared/types/src/dependency-graph.ts`
- [ ] `packages/repo-intelligence/src/dependency_graph.py` parses requirements.txt (PEP 508)
- [ ] Parses pyproject.toml [dependencies] and [optional-dependencies]
- [ ] Extracts external vs internal dependencies
- [ ] Returns list of `DependencyEdge` (importer → package, version, is_external)
- [ ] Handles missing files gracefully (empty graph, no error)

**Files:**
- Create: `shared/types/src/dependency-graph.ts`
- Create: `packages/repo-intelligence/src/dependency_graph.py`
- Modify: `packages/repo-intelligence/src/__init__.py` (export)

---

### Task 3: ModuleDetector (identify Python packages)
**Est.:** 45 min  
**Depends on:** task-002 (PythonAdapter + file listing)  
**Acceptance:**
- [ ] `ModuleDetector` class in `packages/repo-intelligence/src/module_detector.py`
- [ ] Scans for `__init__.py` to identify packages
- [ ] Detects namespace packages (PEP 420, no `__init__.py`)
- [ ] Returns `Module` objects with name, root, type (namespace | regular), files
- [ ] Handles edge cases (empty `__init__.py`, deeply nested)
- [ ] Fast (< 100ms for typical repos)

**Files:**
- Create: `packages/repo-intelligence/src/module_detector.py`
- Create: `shared/types/src/module.ts` (Module interface)
- Modify: `packages/repo-intelligence/src/__init__.py` (export)

---

### Task 4: IncrementalIndexer (git diff based)
**Est.:** 60 min  
**Depends on:** Tasks 1–3 complete  
**Acceptance:**
- [ ] `IncrementalIndexer` class in `packages/repo-intelligence/src/incremental_indexer.py`
- [ ] Computes git diff (added/modified/deleted files since last indexed_at)
- [ ] Re-indexes only changed files (skip unchanged)
- [ ] Updates symbol registry, call graph, import graph incrementally
- [ ] Stores last_indexed_at timestamp
- [ ] Handles initial index (all files treated as "modified")
- [ ] Returns delta: (added_symbols, modified_symbols, removed_symbols)
- [ ] Fast re-index (< 5s for 50-file change)

**Files:**
- Create: `packages/repo-intelligence/src/incremental_indexer.py`
- Modify: `packages/repo-intelligence/src/__init__.py` (export)
- Modify: `shared/storage/` (add last_indexed_at column if needed)

---

### Task 5: Watch mode + `ortho index` CLI command
**Est.:** 60 min  
**Depends on:** Tasks 1–4 complete  
**Acceptance:**
- [ ] `ortho index` (full re-index from scratch)
- [ ] `ortho index --watch` (incremental, polls every 2s, auto re-indexes on change)
- [ ] Watch mode outputs: "Indexed X symbols, Y calls, Z deps"
- [ ] Press Ctrl+C to exit watch mode gracefully
- [ ] Handles file system events (add, modify, delete)
- [ ] No errors on permission denied (skip file, log, continue)
- [ ] `--verbose` flag shows per-file re-index progress

**Files:**
- Modify: `apps/cli/src/commands/index.ts` (new command)
- Modify: `apps/cli/src/cli.ts` (register command)

---

## Task Dependencies

```
Task 1 (CallGraphBuilder)
  ↓
Task 2 (DependencyGraphBuilder) — parallel with Task 3
Task 3 (ModuleDetector) ← 
  ↓
Task 4 (IncrementalIndexer)
  ↓
Task 5 (Watch mode + CLI)
```

Sequential critical path: 1 → 2/3 (parallel) → 4 → 5

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| pyan3 misses dynamic calls | HIGH | Confidence scores < 1.0 flag uncertain edges; document limitation |
| Git diff fails (not a repo) | MEDIUM | Check .git exists, fail gracefully with error message |
| Watch mode consumes CPU | MEDIUM | Debounce file events (100ms), sleep 2s between polls |
| Requirements.txt malformed | LOW | Try/except + log, skip malformed lines |
| Module detection slow (deep nesting) | MEDIUM | Cache results, re-detect only on file add/delete |

---

## Definition of Done

- [ ] All 5 atomic tasks completed
- [ ] All files created/modified per spec
- [ ] No over-engineering (no extra classes, no speculative features)
- [ ] Acceptance criteria are testable and binary
- [ ] Ready for ARCHITECT review

---

## Acceptance Criteria (from spec.md)

1. Call graph builder extracts function calls from Python AST
2. Call graph handles async/await, walrus, match statements
3. Dependency graph parses requirements.txt and pyproject.toml
4. Module detector identifies packages and namespace packages
5. Incremental indexer computes diff and re-indexes only changed files
6. `ortho index` command indexes from scratch
7. `ortho index --watch` monitors for changes and re-indexes
8. Watch mode outputs progress and handles Ctrl+C
9. All file I/O handles errors gracefully
10. Fast (full index < 30s, incremental re-index < 5s)

---

## Out of Scope (intentional)

- Visualizing call graphs (Phase 2+)
- TypeScript/Go adapters (Week 7–8 task scope creep not allowed)
- Dependency vulnerability scanning (future feature)
- Performance optimization beyond "fast enough" (< 30s)

---

*PLANNER session complete. Awaiting GATE 1 approval to proceed to ARCHITECT.*
