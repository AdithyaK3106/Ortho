---
name: task-010-rollback
type: rollback-plan
task_id: task-010-adr-awareness-reporting
---

# Rollback Plan: Task-010 (ADR Awareness + Reporting)

## Failure Scenarios & Recovery

### Scenario 1: Implementation Incomplete or Broken (Pre-Merge)

**Trigger:** BUILDER reports critical bugs, or VERIFIER Phase C shows > 5 test failures not marked xfail.

**Recovery:**

```bash
# 1. Identify last good commit (before task-010 started)
git log --oneline | grep "task-009\|GATE 6"
# Note commit hash

# 2. Reset branch to last known good state
git reset --hard <hash>

# 3. Verify reset successful
git status

# 4. Clean up partial task artifacts
rm -rf .ases/tasks/task-010-*
rm -rf .ases/evidence/task-010/
rm -rf packages/arch-intelligence/src/arch_intelligence/adr_tracker.py
rm -rf packages/arch-intelligence/src/arch_intelligence/reuse_detector.py
rm -rf packages/arch-intelligence/tests/test_adr_tracker.py
rm -rf packages/arch-intelligence/tests/test_reuse_detector.py

# 5. Verify no uncommitted changes
git status
# Expected: "nothing to commit, working tree clean"

# 6. Re-plan: update spec, restart PLANNER
```

**Verify Nothing Lost:**
- task-001 through task-009 all still present and passing
- No regressions in existing packages
- `.ortho/` database unaffected

---

### Scenario 2: `--impact` CLI Fix Breaks Existing `ortho analyze` Behavior

**Trigger:** Regression in `AnalyzeCommand.run` (architecture/layer/subsystem detection) after the
graph-loading fix lands, since this task touches existing code (analyze.py:31-34), not just new files.

**Recovery:**

```bash
# 1. Isolate the --impact fix commit (should be its own atomic commit per plan.md Task 5)
git log --oneline | grep "impact.*fix\|analyze.py"

# 2. Revert just that commit, keep ADRTracker/ReuseDetector commits
git revert <impact-fix-commit-sha>

# 3. Confirm ortho analyze (non-impact paths) passes existing task-008 tests again
pytest packages/arch-intelligence/tests/ -v

# 4. Re-attempt the --impact fix in a new BUILDER session with the regression documented
```

**Why isolated:** plan.md requires Task 5 (CLI integration + --impact fix) to be its own commit
specifically so this fix can be reverted independently of the new ADRTracker/ReuseDetector code,
which don't touch existing files at all.

---

### Scenario 3: Implementation Merged, Then Failures Discovered

**Trigger:** Regressions detected post-merge, or critical bugs found during GATE 6 review.

**Recovery:** Use `git revert` (preserves history).

```bash
# 1. Identify commit to revert
git log --oneline | grep task-010

# 2. Create revert commit (preserves history on main)
git revert <hash> --no-edit

# 3. Document revert in ADR (required for published rollbacks)
# .ases/architecture/adrs/ADR-011-revert-task-010.md
# Status: ACCEPTED (Reverted)
# Context: [failure mode]
# Decision: Revert commit <hash>
# Consequences: ADR-check/reuse/impact-fix unavailable until re-implemented
# Evidence: .ases/evidence/task-010/test-<hash>.log

# 4. Clean up local task artifacts
rm -rf .ases/tasks/task-010-*
rm -rf .ases/evidence/task-010/
```

---

### Scenario 4: Environment Issue (Missing Dependencies)

**Trigger:** TEST-DESIGNER or VERIFIER Phase A fails on import.

**Cause:** ReuseDetector's Levenshtein-distance step needs a dependency not yet installed (stdlib
`difflib.SequenceMatcher` is the ponytail-mode default — only escalate to a new dependency if
sequence lengths make difflib too slow in practice, and document why in implementation-notes.md).

**Recovery:**

```bash
# 1. Prefer stdlib difflib.SequenceMatcher.ratio() first — no new dependency needed
python -c "from difflib import SequenceMatcher; print(SequenceMatcher(None, ['a','b'], ['a','c']).ratio())"

# 2. Only if a dedicated dependency proves necessary (documented performance failure):
pip install python-Levenshtein
# add to packages/arch-intelligence/pyproject.toml

# 3. Verify import works
python -c "import arch_intelligence; print('OK')"

# 4. Re-run VERIFIER Phase A
mkdir -p .ases/evidence/task-010
python -c "import arch_intelligence" 2>&1 | tee .ases/evidence/task-010/import-check.log
echo "EXIT: $?" >> .ases/evidence/task-010/import-check.log
```

**No need to reset branch** — dependency issues are recoverable via pip + commit.

---

### Scenario 5: Performance Issues (ReuseDetector Timeout)

**Trigger:** Full test suite or real-repo scan test takes too long on symbol sets in the hundreds+.

**Recovery:**

```bash
# 1. Identify slow test from pytest output
# "test_reuse_large_symbol_set TIMEOUT"

# 2. Verify bucketing (Symbol.type, line_count // 5) is actually reducing comparison count
# — this is the documented perf guard in spec.md; if bucketing isn't applied correctly, fix it
# before reaching for a smaller test fixture

# 3. If still slow after bucketing, cap real-repo test scope (fewer files) and document the
#    ceiling in spec.md Known Limitations (already anticipated: "ceiling documented")

# 4. Re-run tests, verify pass with adjusted expectations
```

---

## Granular Rollback: Per-Component

```bash
# ADRTracker and ReuseDetector are independent — revert either without affecting the other
git log --oneline | grep "ADRTracker\|adr_tracker"
git revert <adr-tracker-commit-sha>

git log --oneline | grep "ReuseDetector\|reuse_detector"
git revert <reuse-detector-commit-sha>

# CLI --impact fix (Scenario 2) is independently revertible from both
```

**Assumption:** Each atomic task from plan.md (ADRTracker core, ADRTracker+ArchitectureModel,
ReuseDetector core, ReuseDetector evidence, CLI integration+impact fix) is its own commit.

---

## Success Criteria for Rollback Completion

- [ ] All commits referencing task-010 removed or reverted
- [ ] `.ases/tasks/task-010-*` and `.ases/evidence/task-010/` deleted (if pre-merge rollback)
- [ ] No uncommitted changes in working tree
- [ ] Existing tests (task-001 through task-009) still pass
- [ ] `git status` shows clean state
- [ ] New attempt documented in CLAUDE.md and status.md

---

## Prevention: Test Early, Test Often

1. **GATE 4 (Test Coverage Review):** Run pilot tests before full approval
2. **Import validation before implementation:** Catch dependency issues early, prefer stdlib difflib
3. **Real repo testing:** Run ADRTracker/ReuseDetector against this repo's own ADRs/packages during
   development, not just at GATE 5
4. **Isolate the `--impact` fix as its own commit** — it's the only change to pre-existing code in
   this task; keep it revertible independent of the two new detector modules

---

*Rollback plan created by PLANNER, 2026-07-02*
*Effective upon GATE 1 approval*
