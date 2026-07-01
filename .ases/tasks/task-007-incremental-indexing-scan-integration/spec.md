---
task_id: task-007
title: Incremental Indexing + ortho scan Integration
phase: 2
weeks: 5-6
pillar: Pillar 1 (Repository Intelligence)
workflow: feature.md
---

# Specification: task-007

## Overview

Integrate incremental indexing (git diff based) with Python symbol/import/call extraction. Implement `ortho scan` command to scan entire Python repos and build searchable index. Implement `ortho index --watch` for development-time re-indexing.

---

## Acceptance Criteria (AC)

### AC1: IncrementalIndexer Refinement
- [ ] Detect changed files via `git diff HEAD` (added, modified, deleted)
- [ ] Skip unchanged files (performance win)
- [ ] Handle merge conflicts gracefully (report, don't crash)
- [ ] Support `--full` flag to ignore git state and re-index everything

### AC2: ortho scan Command
- [ ] Discover all Python files (recursive walk, exclude .ortho/, __pycache__, .git)
- [ ] Extract symbols (functions, classes, methods) for each file
- [ ] Build import graph (track file dependencies)
- [ ] Build call graph (track function/method calls)
- [ ] Persist to SQLite (indexing table with file, symbol, import, call data)
- [ ] Report results (counts: files, symbols, imports, calls, errors)

### AC3: ortho index --watch Command
- [ ] Watch for file changes (watchdog library or native fs events)
- [ ] Detect added/modified/deleted files
- [ ] Re-index changed files only (use AC1 logic)
- [ ] Report changes in real time
- [ ] Handle Ctrl+C gracefully (cleanup, exit code 0)

### AC4: Error Handling & Resilience
- [ ] Skip syntax errors (log warning, continue with other files)
- [ ] Skip permission errors (log warning, continue)
- [ ] Report summary of errors at end (count, sample)
- [ ] Exit with code 0 if ≥90% files succeeded (acceptable error rate)

### AC5: Zero Regressions
- [ ] All existing tests still pass (SymbolExtractor, ImportGraphBuilder, CallGraphBuilder, ModuleDetector)
- [ ] No breaking changes to existing APIs
- [ ] Backward compatible with stored data

---

## Test Plan Preview (from status.md baseline)

**Expected Test Metrics:**
- Unit tests: 25+ (one per AC sub-task)
- Integration tests: 15+ (end-to-end scanning on test fixtures)
- Real-repo tests: 3+ (integration tests on real Python codebases)
- Total: 43+ tests
- Coverage: ≥85%
- Pass rate: 100% (no failing tests; edge cases marked xfail if any)

**Known Acceptable Failures:** None anticipated. All features required for scanning a Python repo are implemented in task-006.

---

## Reference Benchmark Environment

**Validation Baseline** — These metrics are informational and used for regression tracking, not release gates. Future measurements may legitimately differ as repositories evolve.

**Repository:** fastapi (Python web framework)  
**Snapshot:** Current HEAD at time of task-007 verification  
**Repository Size:** ~60 Python files, ~50 KLOC  

**Observed Metrics (fastapi scan):**
- Symbols extracted: ~87 (functions, classes, methods)
- Calls identified: ~150 (function/method calls)
- Imports tracked: ~84 (from/import statements)
- Scan errors: 0 (100% success rate on codebase)

**Performance Benchmark Environment:**
- Hardware: Standard workstation (8+ core CPU, 8+ GB RAM)
- Storage: SSD, cold cache (fresh database at start of scan)
- Scan type: Full `ortho scan` (no incremental optimization)
- OS: Linux/macOS/Windows (platform-independent expectations)

**Observed Performance:**
- `ortho scan` completes in <5 seconds on fastapi
- `ortho index --watch` detects file changes within 500ms on test fixtures
- These are reference points for regression tracking; variations due to hardware/OS are acceptable

**Usage:** Compare future benchmark runs against these baselines to detect performance regressions.

---

## Implementation Scope

### What IS In Scope
1. Incremental indexer refinement (git diff logic)
2. `ortho scan` command (full repo indexing)
3. `ortho index --watch` command (live re-indexing)
4. Integration with existing symbol/import/call extractors
5. Error handling and resilience
6. Tests and verification

### What IS NOT In Scope
1. Semantic search (deferred to task-004 ContextHub integration)
2. Architecture detection (task-008)
3. CI/CD pipelines (Phase 3)
4. GUI or web UI (beyond scope)
5. Non-Python languages (task-002 TypeScript adapter pending)

---

## Dependencies

### Internal
- `packages/repo-intelligence/src/symbol_extractor.py` (SymbolExtractor)
- `packages/repo-intelligence/src/import_graph.py` (ImportGraphBuilder)
- `packages/repo-intelligence/src/call_graph.py` (CallGraphBuilder)
- `packages/repo-intelligence/src/module_detector.py` (ModuleDetector)
- `packages/repo-intelligence/src/incremental_indexer.py` (IncrementalIndexer)

### External
- `tree-sitter` (==0.20.4) — AST parsing
- `tree-sitter-languages` (==1.9.1) — Python grammar
- `gitpython` — git diff operations
- `watchdog` — file system monitoring (for --watch)
- `click` — CLI argument parsing

---

## Success Metrics

**Functional Acceptance (Release Gates):**

After implementation and verification:
- [ ] All 5 acceptance criteria fully implemented (AC1–AC5)
- [ ] All 43+ tests pass (or edge cases marked xfail + documented)
- [ ] No regressions in existing test suites (SymbolExtractor, ImportGraphBuilder, CallGraphBuilder, ModuleDetector, ModuleDetector)
- [ ] Code quality: clean patterns, proper error handling, no security issues
- [ ] 100% of `ortho scan` and `ortho index --watch` functionality works as specified

**Engineering Quality (Performance Benchmarks):**

These measurements validate that the implementation is efficient, not that it is correct. Performance targets are supplementary to functional acceptance.

- [ ] `ortho scan` completes on reference repository (fastapi) in <5 seconds
- [ ] `ortho index --watch` detects file changes in <500ms (measured on test fixtures)
- [ ] Incremental indexing skips unchanged files (verified via git diff behavior)

**Note:** Performance verification is conducted on the reference benchmark environment (see "Reference Benchmark Environment" section). Results on different hardware, repositories, or operating systems may vary.

---

## References

- FRD Section 16 (Development Roadmap, task-007)
- status.md (Phase 2 Plan, Week 5–6)
- ortho-v3-frd.md (Pillar 1 scope)
- CLAUDE.md (Test Execution Policy, ASES workflow)
