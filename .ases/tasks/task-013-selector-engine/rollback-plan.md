# task-013: Rollback Plan

**Task:** Selector Engine + Execution (Weeks 17–18)  
**Triggers:** Test failures, code review blocks, database corruption  
**Rollback Windows:** Local (not yet merged) vs. Published (after merge)

---

## Rollback Triggers

### GATE 5: Verification Failed
**Condition:** Tests fail, regressions, or database migrations corrupt `.ortho/ortho.db`

**Example Failures:**
- Approval gate infinite loop (never resumes)
- Workflow state not persisted (reload from DB returns null)
- Regression: existing task-012/011/010 tests fail
- Migration 003 corrupts artifact/symbol tables

**Decision:** BUILDER fixes issue and resubmits, OR feature is rejected

---

### GATE 6: Code Review Blocks
**Condition:** REVIEWER finds security, API, or architecture issues that require rework

**Example Issues:**
- Agent invocation uses unvalidated user input (injection risk)
- Approval gate can be bypassed via API
- Circular dependency introduced (executor imports agent, agent imports executor)

**Decision:** BUILDER reworks specific issues and resubmits, OR feature is rejected

---

## Rollback Procedure

### Scenario 1: Local (Not Yet Merged)

**Status:** Code written, tests failing, before human commits to git  
**Rollback Trigger:** GATE 5 or GATE 6 blocks approval

**Steps:**
```bash
# Hard reset to before task-013 started
cd /path/to/ortho
git reset --hard HEAD~5

# Verify state (task-012 still intact)
git log --oneline -10
# Should show: task-012 most recent commit
# Task-013 commits gone

# Optional: clean working tree
git clean -fd

# Verify imports still work
python -c "from packages.orchestration.intent import IntentRouter, IntentClassification"
echo "✓ Task-012 imports work"

# Run task-012 tests to confirm no regression
pytest packages/orchestration/tests/ -v --tb=short -k "test_intent or test_registry"
# Should pass (same as before task-013)
```

**Rollback Triggers (any of these):**
- `git status` shows 5+ new commits with names starting with task-013
- `.ases/tasks/task-013-*` directory exists
- `packages/orchestration/src/selector/` directory exists
- `packages/orchestration/src/executor/` directory exists

---

### Scenario 2: Published (After Human Commits)

**Status:** Code merged to main, tests passing, but post-merge issue discovered (e.g., production crash)  
**Rollback Trigger:** GATE 6 REVIEWER finds blocking issue after merge

**Steps:**
```bash
# Create revert commits (non-destructive)
git log --oneline -10
# Identify task-013 commits (5 commits with timestamps matching task start)

# Example: commits abc1234..xyz5678 are task-013
git revert --no-edit abc1234^..xyz5678  # revert all 5 commits (oldest → newest)

# This creates NEW commits that undo task-013 changes
# (git revert is safer than git reset for published code)

# Verify revert worked
pytest packages/orchestration/tests/ -k "test_intent or test_registry"
# Should pass (task-012 only)

# Push revert commits
git push origin main

# Clean up (optional)
rm -rf .ases/tasks/task-013-selector-engine/
```

**Revert Commit Message:**
```
Revert task-013: Selector Engine + Execution

Reason: [Security issue | Regression | Architecture violation]
Related commits: [ABC1234] [XYZ5678] [...]
Affected: approval gates, state persistence, integration tests

All changes to selector/, executor/, and new CLI commands undone.
Task-012 (Intent Router) remains functional.
```

---

## Verification After Rollback (Local)

```bash
# 1. Check git state
git status
# Output: nothing to commit, working tree clean

# 2. Check task-013 files removed
test -d packages/orchestration/src/selector && echo "ERROR: selector/ still exists" || echo "✓ selector/ removed"
test -d packages/orchestration/src/executor && echo "ERROR: executor/ still exists" || echo "✓ executor/ removed"
test -f apps/cli/src/commands/run.ts && echo "ERROR: run.ts still exists" || echo "✓ run.ts removed"

# 3. Verify task-012 still works
python -c "from packages.orchestration.intent import IntentRouter, IntentClassification" && echo "✓ Task-012 imports OK"
pytest packages/orchestration/tests/test_intent_router.py -v --tb=short
# Should pass (same results as before task-013 started)

# 4. Verify no orphaned DB tables
python -c "
from packages.context_hub.src.store import OrthoDatabase
from pathlib import Path
db = OrthoDatabase(Path('.'))
conn = db.connection()
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print('Tables:', [t[0] for t in tables])
# Should NOT include: workflow_runs, execution_steps
" && echo "✓ No orphaned tables"

# 5. Full regression test
pytest packages/ -v --tb=short
# All tests that passed before task-013 should still pass
```

---

## Verification After Rollback (Published)

```bash
# Same as local, but also verify git history
git log --oneline -10
# Should show: revert commits (e.g., "Revert task-013: ...") at top
# Original task-013 commits still in history (below revert)

# Verify revert is complete
git diff main..HEAD --name-only
# Should be empty (no pending changes)

# Verify tests still pass
pytest packages/ -v --tb=short
# No regressions from revert
```

---

## Migration 003 Cleanup (Critical for Rollback)

**Responsibility:** BUILDER (task-013) owns rollback cleanup for migration 003

**Cleanup Procedure:**

If migration 003 (workflow schema) was already applied before rollback, execute this cleanup:

```python
# Manual cleanup (one-time after rollback)
from pathlib import Path
from packages.context_hub.src.store import OrthoDatabase

db = OrthoDatabase(Path('.'))
conn = db.connection()

# Drop task-013 tables (in dependency order)
try:
    conn.execute("DROP TABLE IF EXISTS approval_gates")
    conn.execute("DROP TABLE IF EXISTS execution_steps")
    conn.execute("DROP TABLE IF EXISTS workflow_runs")
    
    # Remove migration entry (optional — keeps history if present)
    conn.execute("DELETE FROM schema_migrations WHERE version = 3")
    
    conn.commit()
    print("✓ Task-013 schema (migration 003) cleaned up successfully")
except Exception as e:
    conn.rollback()
    print(f"✗ Cleanup failed: {e}")
    raise
```

**Verification After Cleanup:**

```bash
# Verify tables are dropped
python -c "
from pathlib import Path
from packages.context_hub.src.store import OrthoDatabase

db = OrthoDatabase(Path('.'))
conn = db.connection()
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%workflow%'\").fetchall()
if tables:
    print(f'✗ ERROR: Tables still exist: {tables}')
else:
    print('✓ All workflow tables dropped')
"
```

**Why Migration Cleanup is Important:**

- Migration 003 creates tables that reference workflow_runs
- Dropping code (rollback) without dropping tables leaves orphaned schema
- Future re-apply of task-013 will fail if old tables exist
- Cleanup ensures clean state for retry or alternative design

**Schema Dependency Order (for cleanup):**

1. Drop `approval_gates` (FK to workflow_runs)
2. Drop `execution_steps` (FK to workflow_runs)
3. Drop `workflow_runs` (root table)

**Acceptance Criteria (GATE 5 Verification):**
- ✓ Migration 003 executes successfully during BUILDER phase
- ✓ VERIFIER validates tables created (SELECT * FROM workflow_runs works)
- ✓ Rollback procedure documented and verified (manual cleanup works)
- ✓ Migration entry tracked in schema_migrations table

---

## Recovery Path After Rollback

If task-013 is rolled back due to fixable issues:

1. **BUILDER** addresses specific issues (security, regression, architecture)
2. **TEST-DESIGNER** (new session) updates tests to cover fixes
3. **VERIFIER** re-runs full suite
4. **REVIEWER** (new session) re-audits code
5. **Human** approves and commits (new PR/attempt)

---

## Escalation

If rollback itself fails (git corruption, DB locked, etc.):

1. **Backup:** `cp -r .ortho .ortho.backup`
2. **Manual state:** Remove task-013 directories by hand
3. **Verify:** Run full test suite
4. **Decide:** Document incident and retry or reject feature entirely

---

*End of Rollback Plan*
