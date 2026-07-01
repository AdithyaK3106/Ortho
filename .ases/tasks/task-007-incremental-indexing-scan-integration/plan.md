---
task_id: task-007
title: Incremental Indexing + ortho scan Integration — Plan
phase: 2
weeks: 5-6
---

# Plan: task-007

## Goals (from spec.md)

1. Refine incremental indexer (git diff based, handle merges)
2. Implement `ortho scan` (discover + extract + persist)
3. Implement `ortho index --watch` (live re-indexing)
4. Error handling (skip syntax errors, report summary)
5. Zero regressions

---

## Approach

### Phase A: Incremental Indexer Refinement
**Goal:** Reliable git diff based file detection

- Git diff logic: `git diff HEAD --name-only --diff-filter=MADR`
  - M: modified
  - A: added
  - D: deleted
  - R: renamed
- Parse into lists: added, modified, deleted
- Handle merge conflicts: Check `git status --porcelain` for "UU" (unmerged), skip or warn
- Support `--full` flag: ignore git state, scan all Python files

**Atomic task:**
1. Enhance `IncrementalIndexer.get_changed_files(strategy='git|full')`
2. Add merge conflict detection
3. Write 5 unit tests (git scenarios, conflicts, --full mode)

---

### Phase B: ortho scan Command
**Goal:** Full repo indexing in one command

- Discover Python files: recursive walk, excludes (.ortho/, __pycache__, .git, .venv)
- Extract symbols: call SymbolExtractor.extract_symbols() for each file
- Extract imports: call ImportGraphBuilder.extract_imports() for each file
- Extract calls: call CallGraphBuilder.extract_calls() for each file
- Persist: store in SQLite (table: files, symbols, imports, calls)
- Report: print summary (files scanned, symbols found, errors)

**Atomic tasks:**
1. FileDiscoverer class (recursive walk, exclusion logic)
2. Indexer class (orchestrate extraction, persist to DB)
3. `ortho scan` CLI command (entry point, argument parsing)
4. Write 10 integration tests (fixtures with test Python files)
5. Test on fastapi (real-repo baseline)

---

### Phase C: ortho index --watch Command
**Goal:** Live re-indexing during development

- Watch for file changes: use watchdog.FileSystemEventHandler
- Detect changes: added, modified, deleted
- Re-index: call Indexer with changed files only (incremental)
- Report: log changes in real time
- Handle Ctrl+C: cleanup, exit 0

**Atomic tasks:**
1. FileWatcher class (watchdog integration)
2. `ortho index --watch` CLI command
3. Write 5 integration tests (simulate file changes)
4. Test on test fixture (not on real codebase)

---

### Phase D: Error Handling & Resilience
**Goal:** Robust scanning that doesn't fail on single errors

- Skip syntax errors: catch SyntaxError, log warning, continue
- Skip permission errors: catch PermissionError, log warning, continue
- Summary report: count errors, show sample (first 3)
- Exit code: 0 if ≥90% success, 1 otherwise

**Atomic tasks:**
1. ErrorHandler class (logging, thresholds)
2. Retry logic for transient errors (permission, file locked)
3. Write 5 error-handling tests (syntax errors, permissions, partial success)

---

### Phase E: Testing & Verification
**Goal:** 100% test coverage of new code

- Unit tests: 25+ (one per sub-task)
- Integration tests: 15+ (end-to-end scanning)
- Real-repo tests: 3+ (fastapi baseline)
- Regression tests: run full suite, ensure zero breaks

**Atomic tasks:**
1. Write test_incremental_indexer_*.py (5 tests)
2. Write test_file_discoverer_*.py (5 tests)
3. Write test_indexer_*.py (10 integration tests)
4. Write test_file_watcher_*.py (5 tests)
5. Write test_error_handling_*.py (5 tests)
6. Write test_ortho_scan_fastapi_*.py (3 real-repo tests)
7. Run full pytest suite, verify zero regressions

---

## Timeline

**Estimated Duration:** 12 hours (full ASES cycle for one person)

- PLANNER: 1h (spec + plan) ✅
- ARCHITECT: 1.5h (architecture review)
- BUILDER: 6h (5 atomic implementation phases)
- TEST-DESIGNER: 1.5h (test plan + sample tests)
- VERIFIER: 1h (full pytest run + logs)
- REVIEWER: 1h (code review + approval)

**Parallelization:** TEST-DESIGNER shadows BUILDER (concurrent, not sequential)

---

## Rollback Plan

If implementation fails or needs reset:

1. **Commit granularity:** Each atomic task = 1 commit (15 commits total)
2. **Rollback strategy:** If Phase B fails, revert to last successful Phase A commit
3. **Recovery:** Restart BUILDER with revised approach

**Example:**
```bash
# If Phase B fails mid-implementation
git revert HEAD~5..HEAD  # Revert last 5 Phase B commits
# Then restart BUILDER with refined plan
```

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| watchdog library incompatible with Windows | Medium | Test early, fallback to polling if needed |
| Git diff fails on freshly initialized repos | Low | Handle `.git` not found, assume --full mode |
| Merge conflicts block scanning | Low | Detect UU status, warn user, skip changed files |
| Performance: scanning large repos takes >10s | Medium | Add progress bar, allow --shallow mode for large repos |
| Syntax errors in user code crash scanner | Low | Error handler catches SyntaxError, logs, continues |

---

## Success Criteria (Verification)

**Functional Acceptance:**
- [ ] All 43+ tests pass (or edge cases marked xfail)
- [ ] All 5 acceptance criteria (AC1–AC5) fully implemented
- [ ] Zero regressions (full pytest suite passes)
- [ ] Code quality: GATE 6 APPROVED

**Engineering Quality (Performance Benchmarks):**
- [ ] `ortho scan` completes on reference repository in <5s
- [ ] `ortho index --watch` detects changes within 500ms (measured on test fixtures)
- [ ] Incremental indexing efficiently skips unchanged files

(Performance targets are supplementary to functional acceptance and verified on the reference benchmark environment.)

---

## Next Steps (After GATE 1 Approval)

1. ARCHITECT reviews plan + FRD alignment → GATE 2
2. BUILDER implements 5 phases (atomic commits) → GATE 3
3. TEST-DESIGNER writes tests (shadow BUILDER) → GATE 4
4. VERIFIER runs pytest (real logs) → GATE 5
5. REVIEWER audits code quality → GATE 6

