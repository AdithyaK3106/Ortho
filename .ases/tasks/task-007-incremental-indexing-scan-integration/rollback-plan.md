---
task_id: task-007
title: Rollback Plan — Incremental Indexing + ortho scan
---

# Rollback Plan: task-007

## Scope

This plan covers rollback scenarios for task-007 implementation. Rollback is executed if:
- BUILDER encounters unresolvable issues
- Regression tests fail (existing tests break)
- Architectural decisions prove flawed
- Schedule delays require descoping

---

## Granularity: Atomic Commits

Each phase is committed atomically. Total: 15 commits.

```
Phase A: IncrementalIndexer refinement (3 commits)
  - commit-1: get_changed_files() with git diff
  - commit-2: merge conflict detection
  - commit-3: --full flag support

Phase B: ortho scan command (5 commits)
  - commit-4: FileDiscoverer class
  - commit-5: Indexer class (orchestration)
  - commit-6: ortho scan CLI command
  - commit-7: integration tests (fixtures)
  - commit-8: real-repo tests (fastapi baseline)

Phase C: ortho index --watch command (3 commits)
  - commit-9: FileWatcher class
  - commit-10: ortho index --watch CLI command
  - commit-11: watch mode integration tests

Phase D: Error handling & resilience (2 commits)
  - commit-12: ErrorHandler class
  - commit-13: error-handling tests

Phase E: Final verification (2 commits)
  - commit-14: regression test suite
  - commit-15: documentation + summary
```

---

## Rollback Scenarios

### Scenario 1: Phase B (ortho scan) Fails

**Trigger:** FileDiscoverer or Indexer has bugs that break existing tests

**Rollback Steps:**

```bash
# Identify last good commit (end of Phase A)
git log --oneline | grep "Phase A"  # <- commit-3

# Revert Phase B commits
git revert HEAD~11..HEAD  # Revert commit-4 through commit-15

# Restart BUILDER with revised plan
# (e.g., simplify FileDiscoverer, use standard library pathlib)
```

**Recovery:**
- Skip Phase B, move to Phase C (watch mode)
- OR revise Indexer approach, restart Phase B
- OR descope ortho scan, keep only --watch mode

---

### Scenario 2: Regression Tests Fail

**Trigger:** Existing tests (SymbolExtractor, ImportGraphBuilder, etc.) break

**Rollback Steps:**

```bash
# Identify which commit introduced regression
git bisect start
git bisect bad HEAD
git bisect good commit-3  # Last known good (Phase A complete)

# Run regression suite at each point
pytest packages/repo-intelligence/tests/ -x

# Once root commit identified:
git revert <root-commit>
git commit -m "Revert regression introduced in <commit>"

# Restart BUILDER from that point
```

**Recovery:**
- Fix the regression (usually an API change or import issue)
- Commit fix separately
- Re-run full regression suite
- Continue with remaining phases

---

### Scenario 3: watchdog Library Incompatibility

**Trigger:** watchdog fails on Windows (as-is or version mismatch)

**Rollback Steps:**

```bash
# Revert Phase C (commit-9, commit-10, commit-11)
git revert HEAD~4..HEAD

# Implement fallback: polling-based file monitor
# OR descope --watch mode (keep ortho scan, skip watch)
```

**Recovery:**
- Use polling with pathlib.Path.stat() instead of watchdog
- OR remove --watch mode from task-007, defer to future sprint

---

### Scenario 4: Performance Issue (Large Repos Slow)

**Trigger:** `ortho scan` on large repos takes >30s (unacceptable)

**Rollback Steps:**

```bash
# Profile the Indexer class
python -m cProfile -s cumtime -m pytest packages/repo-intelligence/tests/test_indexer_performance.py

# Identify bottleneck (symbol extraction? disk I/O? DB writes?)

# Rollback to commit-5 (Indexer class) if needed
git revert HEAD~10..HEAD

# Optimize approach:
# - Batch DB writes (100 files at a time instead of 1)
# - Parallelize extraction (multiprocessing.Pool)
# - Cache tree-sitter parsers
```

**Recovery:**
- Re-implement optimized Indexer
- Re-run performance tests
- Target: <5s for fastapi (87 symbols)

---

### Scenario 5: GATE 5 (Verification) Fails

**Trigger:** Tests don't pass, coverage <85%, or import errors

**Rollback Steps:**

```bash
# Check import validation (pre-flight)
python -c "import packages.repo_intelligence" 2>&1

# Check test errors
pytest packages/repo-intelligence/tests/test_*.py -v 2>&1 | head -50

# If import fails: fix __init__.py or missing dependencies
# If tests fail: identify which test, assign to BUILDER to fix

# If >=3 tests fail: escalate to PLANNER, consider descoping
```

**Recovery:**
- BUILDER fixes identified issues
- TEST-DESIGNER adjusts tests if needed
- Re-run GATE 5 verification
- Proceed to GATE 6 if all green

---

### Scenario 6: Complete Failure (Uncoverable)

**Trigger:** Architecture fundamentally broken, multiple unresolvable issues

**Rollback Steps:**

```bash
# Revert entire task-007 to pre-BUILDER state
git revert task-006..HEAD  # Revert all task-007 commits

# Restart task-007 PLANNER with lessons learned
# Document in implementation-notes.md what failed and why
```

**Recovery:**
- Descope task-007, split into smaller tasks
- OR defer to later phase
- OR redesign architecture with ARCHITECT

---

## Emergency Descope

If timeline pressure requires descoping:

**Option A: Keep ortho scan, Skip watch mode**
```bash
# Revert Phase C, D, E (commit-9 onward)
git revert HEAD~6..HEAD

# Deploy with ortho scan only
# Defer ortho index --watch to task-007b (future sprint)
```

**Option B: Keep minimal scan, Skip incremental + error handling**
```bash
# Revert Phase A, D (3 + 2 commits)
git revert HEAD~4..HEAD HEAD~13..HEAD~11

# Deploy with basic ortho scan (no incremental, basic error handling)
# Replan Phases A + D for task-007b
```

**Option C: Defer entire task**
```bash
# Revert all task-007 work
git revert task-006..HEAD

# Close task-007, open task-007b with revised scope
# Continue with task-008 (Architecture Detection) instead
```

---

## Testing During Rollback

After any rollback:

```bash
# Step 1: Validate imports
python -c "import packages.repo_intelligence" 2>&1

# Step 2: Run regression suite
pytest packages/repo-intelligence/tests/ -v --tb=short 2>&1 | tee rollback-test.log

# Step 3: Check exit code
echo "Exit code: $?"

# Step 4: If all pass, proceed; if fail, escalate
```

---

## Decision Tree

```
Is implementation failing?
├─ YES: Identify failing phase (A, B, C, D, E)
│   ├─ Phase A or B: Revert to last phase boundary, restart BUILDER
│   ├─ Phase C (watchdog): Implement polling fallback or descope
│   ├─ Phase D (errors): Simplify error handling, keep core scanning
│   └─ Phase E (tests): Fix tests or mark as xfail, escalate if >3 failures
│
└─ NO: Proceed to next gate (ARCHITECT → GATE 2)

Are regressions detected?
├─ YES: Run git bisect, identify root commit, fix or revert
└─ NO: Continue

Is performance unacceptable?
├─ YES: Profile, identify bottleneck, optimize or descope
└─ NO: Proceed to GATE 6 (REVIEWER)

Is timeline threatened?
├─ YES: Emergency descope (Option A, B, or C above)
└─ NO: Finish all 5 phases
```

---

## Checkpoints (Critical Moments)

1. **After Phase A:** Regression suite passes ✓
2. **After Phase B:** `ortho scan` works on test fixtures ✓
3. **After Phase C:** `ortho index --watch` detects changes ✓
4. **After Phase D:** Error handling doesn't hide bugs ✓
5. **After GATE 5:** All tests pass, coverage ≥85% ✓

If any checkpoint fails → evaluate rollback using decision tree above.

---

## Key Files to Preserve

- `.ases/tasks/task-007-*/spec.md` (spec, never roll back)
- `.ases/tasks/task-007-*/plan.md` (plan, update if revised)
- `.ases/tasks/task-007-*/rollback-plan.md` (this file, update if scenarios change)
- `packages/repo-intelligence/src/*.py` (implementation, subject to rollback)
- `packages/repo-intelligence/tests/test_*.py` (tests, subject to rollback)

If rollback occurs, update `implementation-notes.md` with what failed and restart from appropriate checkpoint.

