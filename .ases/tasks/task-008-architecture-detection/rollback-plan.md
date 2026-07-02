# task-008: Architecture Detection — Rollback Plan

**Task ID:** task-008  
**Rollback Target:** task-007 final commit (1d7cbec)  
**Estimated Rollback Time:** 5–10 minutes

---

## Rollback Policy

**Principle:** Preserve auditability and history. Use `git revert` for published work; `git reset --hard` only for unpublished local changes.

---

## Rollback Triggers

Rollback initiated if ANY of the following occur:

1. **Test Failure Rate >10%** — More than 6 of 65+ tests fail and cannot be fixed within 1 session
2. **Regression in Existing Packages** — repo-intelligence or context-hub tests fail (exit ≠ 0)
3. **Architecture Review Rejection** — GATE 2 rejected with unsalvageable design issues
4. **Import Failures** — `packages.arch_intelligence` cannot be imported after build
5. **Circular Dependencies Introduced** — Dependency analysis shows cycle in package import chain

---

## Rollback Strategy: Local vs. Published

### For Unpublished Local Work (During Development)

**Condition:** Changes exist only in working tree or local commits; not yet pushed or used as verification evidence.

**Why:** Local work has not created evidence artifacts or verification traces. Hard reset is fastest and safest.

**Procedure:**

```bash
# Discard all uncommitted changes
git restore .

# Reset to last-known-good commit
git reset --hard 1d7cbec

# Delete new directories
rm -rf packages/arch-intelligence/
rm -rf .ases/tasks/task-008-architecture-detection/
rm -rf .ases/evidence/task-008/

# Verify clean state
git status
```

---

### For Published Work (After GATE Commits)

**Condition:** Work has been committed and used as verification evidence; changes are part of the repository history.

**Why:** Published work must preserve auditability. History and evidence remain intact for post-incident analysis.

**Procedure:**

```bash
# Identify all task-008 commits (newest first)
git log --oneline 1d7cbec..HEAD

# Revert in reverse chronological order (newest first)
# This creates new commits that undo each change
git revert --no-edit [newest-commit-hash]
git revert --no-edit [second-newest-commit-hash]
# ... repeat for all task-008 commits

# Verify history is preserved
git log --oneline -10
```

**Result:** Creates new revert commits while preserving full history.

**Justification:**
- Preserves auditability (evidence and commits remain traceable)
- Maintains history for post-incident analysis
- Allows recovery of specific components if only partial rollback needed
- Aligns with ASES requirement that engineering decisions be documented

---

## Step-by-Step Rollback Execution

### Phase 1: Identify Rollback Point

```bash
# List recent commits
git log --oneline -20

# Identify task-007 final commit
# Expected: commit 1d7cbec with message "Add comprehensive real-repo verification report"
ROLLBACK_COMMIT="1d7cbec"
echo "Rollback target: $ROLLBACK_COMMIT"
```

### Phase 2: Determine Strategy

```bash
# Check if changes have been committed
COMMITS_SINCE_BASE=$(git log --oneline $ROLLBACK_COMMIT..HEAD | wc -l)

if [ $COMMITS_SINCE_BASE -eq 0 ]; then
  echo "Local work only (no commits) — using git reset --hard"
  STRATEGY="local"
else
  echo "Published commits found ($COMMITS_SINCE_BASE) — using git revert"
  STRATEGY="published"
fi
```

### Phase 3A: Local Rollback (if no commits since base)

```bash
git restore .
git reset --hard 1d7cbec
rm -rf packages/arch-intelligence/
rm -rf .ases/tasks/task-008-architecture-detection/
rm -rf .ases/evidence/task-008/
git status
```

### Phase 3B: Published Rollback (if commits exist)

```bash
# Get all task-008 commits in reverse chronological order
COMMITS=$(git log --oneline 1d7cbec..HEAD --reverse | awk '{print $1}')

# Revert each in reverse order (newest first)
for COMMIT in $(echo "$COMMITS" | tac); do
  echo "Reverting $COMMIT..."
  git revert --no-edit $COMMIT
done

# Verify history preserved
git log --oneline -10
```

### Phase 4: Verify Rollback Success

```bash
# Check imports work
python -c "import packages.repo_intelligence" && echo "✓ repo-intelligence imports OK"
python -c "import packages.context_hub" && echo "✓ context-hub imports OK"

# Run regression tests
pytest packages/repo_intelligence/tests/ packages/context_hub/tests/ -v
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✓ Rollback successful — all existing tests pass"
else
  echo "✗ FAILED — existing tests still failing"
  exit 1
fi
```

### Phase 5: Document Rollback Event

Update CLAUDE.md with the incident:

```markdown
## Rollback Event — task-008

**Date:** [YYYY-MM-DD HH:MM UTC]  
**Trigger:** [Test failures / Regression / Architecture rejection / Other]  
**Strategy Used:** [git reset --hard (local) / git revert (published)]  
**Base Commit:** 1d7cbec  
**Result:** Rollback VERIFIED — all existing tests pass  
**Next Action:** [PLANNER revises plan, ARCHITECT reviews, or task rejected]
```

---

## Rollback Verification Checklist

After rollback completes, verify all of:

- [ ] All changes properly reverted or undone
- [ ] Working directory is clean (`git status` shows no changes or only revert commits)
- [ ] HEAD is at correct position (after rollback)
- [ ] `packages/arch-intelligence/` does not exist
- [ ] `packages.repo_intelligence` imports successfully
- [ ] `packages.context_hub` imports successfully
- [ ] All repo-intelligence tests pass (exit 0)
- [ ] All context-hub tests pass (exit 0)
- [ ] Full git history is intact (if using revert: all commits visible in log)

---

## Rollback Timings

| Operation | Time |
|-----------|------|
| Identify commits | 1 min |
| Choose strategy | <1 min |
| Execute rollback | 1–2 min |
| Verify imports | 1 min |
| Run tests | 3–5 min |
| Document event | 1 min |
| **Total** | 7–10 min |

---

## Quick-Start Commands

### Local rollback (copy-paste)

```bash
#!/bin/bash
set -e
git restore .
git reset --hard 1d7cbec
rm -rf packages/arch-intelligence/
rm -rf .ases/tasks/task-008-architecture-detection/
rm -rf .ases/evidence/task-008/
python -c "import packages.repo_intelligence" && echo "✓ repo-intelligence OK"
python -c "import packages.context_hub" && echo "✓ context-hub OK"
pytest packages/repo_intelligence/tests/ packages/context_hub/tests/ -v
echo "✓ Rollback VERIFIED"
```

### Published rollback (copy-paste)

```bash
#!/bin/bash
set -e
COMMITS=$(git log --oneline 1d7cbec..HEAD --reverse | awk '{print $1}')
for COMMIT in $(echo "$COMMITS" | tac); do
  echo "Reverting $COMMIT..."
  git revert --no-edit $COMMIT
done
python -c "import packages.repo_intelligence" && echo "✓ repo-intelligence OK"
python -c "import packages.context_hub" && echo "✓ context-hub OK"
pytest packages/repo_intelligence/tests/ packages/context_hub/tests/ -v
echo "✓ Rollback VERIFIED"
```

---

*Rollback plan prepared by PLANNER role.*  
*Documented for emergency use if task-008 fails catastrophically.*
