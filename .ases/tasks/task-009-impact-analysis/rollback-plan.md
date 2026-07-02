---
name: task-009-rollback
type: rollback-plan
task_id: task-009-impact-analysis
---

# Rollback Plan: Task-009 (Impact Analysis + Debt Scoring)

## Failure Scenarios & Recovery

### Scenario 1: Implementation Incomplete or Broken (Pre-Merge)

**Trigger:** BUILDER reports critical bugs, or VERIFIER Phase C shows > 5 test failures not marked xfail.

**Recovery:**

```bash
# 1. Identify last good commit (before task-009 started)
git log --oneline | grep "task-008\|GATE 6"
# Note commit hash (e.g., 650187c)

# 2. Reset branch to last known good state
git reset --hard 650187c

# 3. Verify reset successful
git status
# Expected: "On branch main. Your branch is up to date with origin/main."

# 4. Clean up partial task artifacts
rm -rf .ases/tasks/task-009-*
rm -rf .ases/evidence/task-009/
rm -rf packages/impact-analysis/  # if partially created

# 5. Verify no uncommitted changes
git status
# Expected: "nothing to commit, working tree clean"

# 6. Re-plan: file issue, update spec, restart PLANNER
```

**Verify Nothing Lost:**
- task-001 through task-008 all still present and passing
- No regressions in existing packages
- `.ortho/` database unaffected

---

### Scenario 2: Implementation Merged, Then Failures Discovered

**Trigger:** Regressions detected post-merge, or critical bugs found during GATE 6 review.

**Recovery:** Use `git revert` (preserves history).

```bash
# 1. Identify commit to revert
git log --oneline | grep task-009
# Note commit hash (e.g., abc1234)

# 2. Create revert commit (preserves history on main)
git revert abc1234 --no-edit

# 3. Document revert in ADR (required for published rollbacks)
cat > docs/adr/ADR-XXX-task-009-revert.md << 'EOF'
# ADR-XXX: Revert Task-009 (Impact Analysis + Debt Scoring)

## Status
Accepted (Reverted)

## Context
Task-009 merged but critical bugs discovered post-merge:
- Circular dependency handling broken in ImpactAnalyzer
- DebtScorer weights not normalized correctly
- Test failures indicate architectural mismatch with repo-intelligence

## Decision
Revert commit abc1234 on main to restore stability.

## Consequences
- Impact/Debt features unavailable until re-implemented
- No data loss (feature was new)
- Allows time to fix root causes

## Evidence
- Test failure log: .ases/evidence/task-009/test-abc1234.log
- Investigation: .ases/tasks/task-009-*/analysis.md
EOF

# 4. Push revert
git push origin main

# 5. Clean up local task artifacts
rm -rf .ases/tasks/task-009-*
rm -rf .ases/evidence/task-009/

# 6. Notify: Task-009 reverted, will restart after root cause analysis
```

**Post-Revert Actions:**
1. Analyze failure logs and document root cause
2. Update spec.md with lessons learned
3. Restart PLANNER phase with corrected assumptions
4. Prevent same bug with stronger unit tests

---

### Scenario 3: Environment Issue (Missing Dependencies)

**Trigger:** TEST-DESIGNER or VERIFIER Phase A fails on import.

**Cause:** Missing gitpython, networkx, or other dependency.

**Recovery:**

```bash
# 1. Identify missing dependency from error log
# Error: "ModuleNotFoundError: No module named 'networkx'"

# 2. Install dependency
pip install networkx gitpython

# 3. Update pyproject.toml to include it
# (add to packages/impact-analysis/pyproject.toml dependencies)

# 4. Verify import works
python -c "import packages.impact_analysis; print('OK')"

# 5. Re-run VERIFIER Phase A (import validation)
mkdir -p .ases/evidence/task-009
python -c "import packages.impact_analysis" 2>&1 | tee .ases/evidence/task-009/import-check.log
echo "EXIT: $?" >> .ases/evidence/task-009/import-check.log

# 6. If still broken, BUILDER fixes __init__.py or pyproject.toml, re-commit
```

**No need to reset branch** — dependency issues are recoverable via pip + commit.

---

### Scenario 4: Scope Creep (Test Count Exceeds Expectation)

**Trigger:** VERIFIER runs tests, finds 100+ instead of 60+. May indicate scope violation.

**Decision Point:**

If test count legitimate (property-based explosion, real integration tests):
- Update spec.md "Expected Test Metrics" to reflect actual count
- Approve GATE 4 with adjusted baseline

If tests reveal scope creep:
- Identify new tasks added beyond spec
- ARCHITECT reviews; if not in plan.md, send back to PLANNER to replan
- Do not merge until scope aligned

---

### Scenario 5: Performance Issues (Tests Timeout)

**Trigger:** Full test suite takes > 5 minutes, or integration tests timeout on real repo.

**Cause:** BFS on large graphs (1000+ symbols) is O(n), slow without optimization.

**Recovery:**

```bash
# 1. Identify slow tests from pytest output
# "test_impact_real_repo.py::test_impact_large_graph TIMEOUT"

# 2. Add performance guards to code
# In ImpactAnalyzer.analyze():
#   if len(visited_nodes) > 1000:
#       warn("Large graph; performance may degrade")
#       # Optional: add memoization or early-exit

# 3. Update test with timeout + reasonable limit
# @pytest.mark.timeout(10)
# def test_impact_large_graph():
#     # Only test up to 1000 nodes, document limit

# 4. Document limitation in spec.md Known Limitations
# 5. Re-run tests, verify pass with adjusted expectations

# 6. If still too slow, consider caching (optional enhancement post-task-009)
```

---

## Granular Rollback: Per-Task

If only one component has issues, can selectively revert:

```bash
# Revert only Task 1 (ImpactAnalyzer) implementation
git log --oneline | grep "Task 1\|ImpactAnalyzer"
# Find commit, revert it

git revert [commit-sha]

# Other components (Tasks 2–4) remain intact
# Allows parallel fixing
```

**Assumption:** Task commits are granular and independent (enforced during BUILDER phase).

---

## Success Criteria for Rollback Completion

- ✅ All commits referencing task-009 removed or reverted
- ✅ `.ases/tasks/task-009-*` and `.ases/evidence/task-009/` deleted
- ✅ No uncommitted changes in working tree
- ✅ Existing tests (task-001 through task-008) still pass
- ✅ `git status` shows clean state
- ✅ New attempt documented in CLAUDE.md or status.md

---

## Prevention: Test Early, Test Often

To avoid needing rollback:

1. **GATE 4 (Test Coverage Review):** Run pilot tests before full approval
2. **Import validation before implementation:** Catch dependency issues early
3. **Real repo testing:** Run on fastapi during development, not just at GATE 5
4. **Granular commits:** Each task 1–4 is its own commit, enabling fine-grained rollback

---

*Rollback plan created by PLANNER, 2026-07-02*
*Effective upon GATE 1 approval*
