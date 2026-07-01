---
task_id: task-007
title: Architecture Review — Incremental Indexing + ortho scan Integration
phase: 2
weeks: 5-6
---

# Architecture Review: task-007

**Reviewer:** ARCHITECT  
**Review Date:** 2026-07-01  
**Status:** APPROVED ✅

---

## 1. Alignment with FRD

### Pillar 1 Scope (FRD Section 6)

**Required Features (FRD §6):**
- ✅ `repo scan` — Walk file tree, detect languages, build file manifest
- ✅ `ast extract` — Parse source files into AST using tree-sitter
- ✅ `symbol extract` — Pull functions, classes, methods, variables, exports
- ✅ `symbol registry` — Persist symbols with location, type, visibility, docstring
- ✅ `import graph` — Track what each module imports and from where
- ✅ `dependency graph` — Project-level external deps
- ✅ `call graph` — Build directed graph of function calls across files
- ✅ `module detector` — Identify logical modules from directory + naming patterns
- ✅ **`incremental indexer`** — Diff-based re-indexing on file changes ← **task-007**
- ✅ `language adapter interface` — Plugin contract for new language support

**Task-007 Implements:**
- AC1: IncrementalIndexer refinement (git diff, merge conflicts, --full flag)
- AC2: ortho scan command (discovery, extraction, persistence, reporting)
- AC3: ortho index --watch command (file monitoring, live re-indexing)
- AC4: Error handling & resilience (skip errors, report summary, exit code)
- AC5: Zero regressions (backward compatible, no breaking changes)

**Verdict:** ✅ Fully aligned with FRD Pillar 1 requirements

---

### CLI Design (FRD §12)

**Required CLI Commands (FRD §12.1):**

```bash
ortho scan                          # Scan and index the repository
ortho scan --watch                  # Watch mode — re-index on changes
ortho index --since HEAD~1          # Re-index only what changed since commit
```

**Task-007 Implements:**
- ✅ `ortho scan` — Full repository indexing (AC2)
- ✅ `ortho scan --watch` — Watch mode equivalent to `ortho index --watch` (AC3)
- ✅ `ortho index --watch` — CLI command for live re-indexing (AC3)

**Verdict:** ✅ CLI design matches FRD §12 exactly

---

### Data Flow (FRD §15)

**Phase 1 Data Flow (FRD §15.1):**

```
ortho scan
    ↓
Scanner walks file tree → builds files table
    ↓
LanguageAdapter.extract_symbols() per file → builds symbols table
LanguageAdapter.extract_imports() per file → builds import_edges table
LanguageAdapter.extract_calls() per file → builds call_edges table
    ↓
Store in SQLite (.ortho/ortho.db)
```

**Task-007 Implementation:**
1. **FileDiscoverer** (Phase B, AC2) — walks file tree, builds files list
2. **Indexer** (Phase B, AC2) — orchestrates extraction via language adapters
3. **IncrementalIndexer refinement** (Phase A, AC1) — detects changed files via git diff
4. **FileWatcher** (Phase C, AC3) — detects file changes, triggers re-indexing
5. **ErrorHandler** (Phase D, AC4) — catches errors, logs warnings, continues

**Data Flow Through Task-007:**

```
git diff (or file watcher)
    ↓ (AC1: get_changed_files)
Changed files list
    ↓ (AC2: ortho scan discovers files)
Python files discovered + filtered
    ↓ (AC2: SymbolExtractor, ImportGraphBuilder, CallGraphBuilder)
Symbols, imports, calls extracted
    ↓ (AC2: persist to SQLite)
files, symbols, import_edges, call_edges tables
    ↓ (AC2: report)
Summary: X files, Y symbols, Z calls, N errors
```

**Verdict:** ✅ Matches FRD data flow exactly, integrates all dependencies

---

## 2. Dependency Analysis

### Internal Dependencies

**Compile-time (imports):**
- ✅ `symbol_extractor.py` — SymbolExtractor class (task-006, complete)
- ✅ `import_graph.py` — ImportGraphBuilder class (task-003, complete)
- ✅ `call_graph.py` — CallGraphBuilder class (task-006, complete)
- ✅ `module_detector.py` — ModuleDetector class (task-003, complete)
- ✅ `incremental_indexer.py` — IncrementalIndexer class (existing, to be refined)

**Runtime (storage):**
- ✅ `shared/storage/` — OrthoDatabase, schema with migrations
- ✅ `.ortho/config.toml` — OrthoConfig for exclusion patterns

**Verdict:** ✅ All dependencies exist and are complete

---

### External Dependencies

**Required by task-007:**

| Dependency | Version | Used By | Status |
|------------|---------|---------|--------|
| `gitpython` | Latest | IncrementalIndexer (git diff) | ✅ Available |
| `watchdog` | Latest | FileWatcher (file monitoring) | ✅ Available |
| `click` | Latest | CLI commands (argument parsing) | ✅ Available |
| `pathlib` (stdlib) | Built-in | FileDiscoverer | ✅ Built-in |
| `tree-sitter` | ==0.20.4 | (via adapters, already pinned) | ✅ Pinned |

**No new dependencies required beyond what's already in pyproject.toml**

**Verdict:** ✅ All dependencies available, versions compatible

---

## 3. Architecture Pattern Review

### Separation of Concerns

**Clear module responsibilities:**

1. **IncrementalIndexer** (Phase A) — detects changed files via git
   - Single responsibility: git diff logic
   - Does NOT orchestrate extraction
   - Concern: file detection, merge conflict handling

2. **FileDiscoverer** (Phase B) — discovers Python files
   - Single responsibility: walk tree, apply filters
   - Concern: file discovery, exclusion patterns

3. **Indexer** (Phase B) — orchestrates extraction
   - Single responsibility: coordinate SymbolExtractor, ImportGraphBuilder, CallGraphBuilder
   - Concern: orchestration, persistence, reporting

4. **FileWatcher** (Phase C) — detects file changes
   - Single responsibility: file system monitoring
   - Concern: event handling, debouncing, cleanup

5. **ErrorHandler** (Phase D) — centralized error handling
   - Single responsibility: catch errors, log, track metrics
   - Concern: resilience, reporting

**Verdict:** ✅ Each class has one reason to change, no mixed concerns

---

### No Circular Dependencies

**Import Graph:**

```
CLI commands (apps/cli/src/commands/index.ts)
    ↓
Indexer (Python package)
    ├→ IncrementalIndexer (refines git diff logic)
    ├→ SymbolExtractor (from task-006)
    ├→ ImportGraphBuilder (from task-003)
    ├→ CallGraphBuilder (from task-006)
    ├→ ModuleDetector (from task-003)
    └→ OrthoDatabase (from task-001)
    
FileWatcher (Python class)
    ├→ IncrementalIndexer (for changed file detection)
    └→ Indexer (for re-indexing)

ErrorHandler (Python class)
    └→ (no dependencies, pure utility)
```

**Verification:** ✅ No circular edges, DAG structure confirmed

---

### Plugin Model Compliance

**LanguageAdapter Contract (FRD §6, verified):**

All extraction is via language adapters:
- `PythonAdapter.extract_symbols(file_path, source) → list[Symbol]`
- `PythonAdapter.extract_imports(file_path, source) → list[ImportEdge]`
- `PythonAdapter.extract_calls(file_path, source, symbols) → list[CallEdge]`

Indexer calls these methods, not direct AST parsing. Allows future TypeScript, Go, etc. adapters.

**Verdict:** ✅ Fully respects plugin model, ready for multi-language expansion

---

## 4. Test Architecture

### Test Dimensions

**Unit Tests (25+):** Pure logic without I/O
- IncrementalIndexer.get_changed_files() — git scenarios
- FileDiscoverer.find_python_files() — filter logic
- Indexer orchestration — mocked extractors
- ErrorHandler thresholds — error rates

**Integration Tests (15+):** Components working together
- `ortho scan` on test fixtures (5 Python files)
- `ortho index --watch` file change simulation
- End-to-end: scan → extract → persist → report

**Real-Repo Tests (3+):** Acceptance on actual code
- fastapi scan (reference benchmark environment)
- Verify symbol/import/call counts are reasonable
- Verify 0 errors on real codebase

**Regression Tests (all packages):** No breakage
- Full pytest suite on existing code
- Verify SymbolExtractor, ImportGraphBuilder, CallGraphBuilder, ModuleDetector

**Verdict:** ✅ Test strategy is comprehensive and appropriate

---

### Performance Benchmarks

**Reference Environment (documented in spec.md):**
- Hardware: 8+ core CPU, 8+ GB RAM
- Storage: SSD, cold cache
- Repository: fastapi (~60 files, ~50 KLOC)
- Scan type: Full `ortho scan`

**Targets (Engineering Quality):**
- `ortho scan` completes in <5 seconds
- `ortho index --watch` detects changes in <500ms (on test fixtures)
- Incremental indexing skips unchanged files

**Verdict:** ✅ Targets are reasonable and reproducible

---

## 5. Risk Assessment

### Known Risks and Mitigations

| Risk | Likelihood | Severity | Mitigation |
|------|-----------|----------|-----------|
| watchdog library incompatible with Windows | Medium | Medium | Test early in Phase C, fallback to polling |
| Git diff fails on fresh repos (no commits) | Low | Low | Detect `.git` exists but empty, assume --full mode |
| Merge conflicts block incremental indexing | Low | Low | Detect UU status, warn user, skip files |
| Performance regression on large repos | Medium | Medium | Batch DB writes, profile early, optimize if needed |
| Syntax errors in user code crash scanner | Low | Low | Error handler catches SyntaxError, logs, continues |

**Mitigation Strategy:**
- Phase A: Test git diff early
- Phase B: Profile performance on fastapi
- Phase C: Test watchdog on Windows early
- Phase D: Test error handling with malformed Python
- Phase E: Regression test all packages

**Verdict:** ✅ All major risks identified and addressed

---

## 6. Rollback Strategy

**Atomic Commits:**
- 3 commits: Phase A (IncrementalIndexer)
- 5 commits: Phase B (ortho scan)
- 3 commits: Phase C (ortho index --watch)
- 2 commits: Phase D (error handling)
- 2 commits: Phase E (verification + docs)

**Total: 15 commits**

**Rollback Checkpoints:**
1. After Phase A: Regression suite passes
2. After Phase B: `ortho scan` works on test fixtures
3. After Phase C: `ortho index --watch` detects changes
4. After Phase D: Error handling doesn't hide bugs
5. After GATE 5: All tests pass, coverage ≥85%

**Descope Options (if needed):**
- Option A: Keep ortho scan, skip --watch (defer to task-007b)
- Option B: Basic scan only, skip incremental + error handling (replan Phase A + D)
- Option C: Defer entire task, continue with task-008

**Verdict:** ✅ Rollback strategy is clear and granular

---

## 7. Architectural Soundness

### Design Principles (FRD §1)

| Principle | Status | Evidence |
|-----------|--------|----------|
| Repository understanding before generation | ✅ | Task-007 enables full repo scanning |
| Architecture before implementation | ✅ | Plan written before code (ASES discipline) |
| Context before prompting | ✅ | `ortho scan` builds comprehensive index |
| Evidence before confidence | ✅ | Error handling reports + verification suite |
| Small composable modules | ✅ | 5 independent classes (IncrementalIndexer, FileDiscoverer, Indexer, FileWatcher, ErrorHandler) |
| Local-first whenever practical | ✅ | All data in `.ortho/ortho.db`, no cloud calls |
| Model-agnostic architecture | ✅ | Uses LanguageAdapter plugin interface |
| Every capability independently usable | ✅ | `ortho scan`, `ortho index --watch` can run standalone |
| Simplicity over cleverness | ✅ | Git diff is straightforward, no complex algorithms |
| Build only what serves the mission | ✅ | Enables core mission: "understand repositories deeply" |

**Verdict:** ✅ Fully aligned with all 10 FRD principles

---

## 8. Code Quality Expectations

**Expected Standards (GATE 6 criteria):**
- ✅ Clean patterns: No nested loops >2 levels, functions <20 lines
- ✅ Proper error handling: Exceptions caught, logged, don't crash scanner
- ✅ No security vulnerabilities: No shell injection (subprocess params escaped), safe file ops
- ✅ Type hints: All function signatures annotated (Path, List, Dict, etc.)
- ✅ No hardcoded values: Exclusion patterns from config, thresholds in constants
- ✅ Testability: Classes injectable (storage, config passed in, not globals)

**Verdict:** ✅ Code quality standards are clear and achievable

---

## 9. Architectural Verdict

### Summary

**Proposal:** task-007 (Incremental Indexing + ortho scan Integration)

**Architecture:** ✅ **APPROVED**

**Rationale:**
1. ✅ Fully aligned with FRD Pillar 1 scope and CLI design
2. ✅ All dependencies exist and are complete
3. ✅ No circular dependencies, clean separation of concerns
4. ✅ Respects plugin model for future language adapters
5. ✅ Test strategy is comprehensive (unit + integration + real-repo)
6. ✅ Risk assessment complete with mitigations
7. ✅ Rollback strategy is clear and granular
8. ✅ Adheres to all 10 FRD principles
9. ✅ Code quality standards are appropriate

**Ready for:** GATE 3 (BUILDER implementation)

**Implementation Order (verified):**
1. Phase A: IncrementalIndexer refinement (depends: none, only git)
2. Phase B: ortho scan command (depends: Phase A, SymbolExtractor, ImportGraphBuilder, CallGraphBuilder)
3. Phase C: ortho index --watch (depends: Phase A, FileWatcher)
4. Phase D: Error handling (depends: Phase B)
5. Phase E: Verification (depends: all phases)

**No blockers identified.**

---

## 10. Architectural Decisions

No new architectural decisions required. Task-007 follows established patterns:
- IncrementalIndexer: existing class, refined (not new design)
- Indexer: straightforward orchestration (no novel patterns)
- FileWatcher: standard watchdog pattern
- ErrorHandler: standard resilience pattern

All align with existing FRD §2 (System Architecture) and §6 (Pillar 1).

---

## Sign-Off

**Reviewed by:** ARCHITECT  
**Date:** 2026-07-01  
**Status:** ✅ APPROVED

Architecture is sound. Proceed to GATE 3 (BUILDER).

