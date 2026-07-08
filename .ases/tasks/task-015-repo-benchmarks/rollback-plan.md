---
title: task-015 Rollback Plan
task: Public Repository Benchmarks
workflow: feature.md
---

# Rollback Plan — task-015

## Risk Profile

**Risk Level:** LOW

This is a benchmarking task. No production code changes. No breaking changes to Ortho itself. Pure analysis of existing Phases 1–3 functionality.

**Trigger conditions for rollback:**
- BUILDER discovers Ortho has a critical bug during benchmarking (e.g., crash on 80% of repos) → **stop, report bug, fix in hotfix task**
- Sampling methodology is flawed (e.g., not stratified correctly) → PLANNER revises spec, BUILDER re-runs
- Manual spot-checks reveal systematic misclassification (e.g., >80% architecture calls wrong) → may indicate Phase 2 regression, investigate before rollback

## Rollback Procedure

### If Rollback Triggered Before GATE 5 (Verification)

**Local cleanup** (most likely case):
1. Delete all benchmark artifacts:
   ```bash
   rm -rf .ases/tasks/task-015-repo-benchmarks/
   rm -rf .ases/evidence/task-015/
   rm -rf /tmp/ortho-benchmark/  # cloned repos
   ```
2. Git status should show clean
3. No commits needed (benchmarks don't land in main)

### If Rollback Triggered After GATE 5 (Published Evidence)

**Published cleanup:**
1. Same local cleanup as above
2. If any results were shared externally or discussed: note the retraction in CLAUDE.md
3. Git status clean; no commits; move forward with corrected task

## Non-Rollback Scenarios (Fix, Don't Revert)

**Scenario: AC2 fails on 5 repos (95% success is acceptable)**
- Action: Document in errors/ directory; exclude from metrics; proceed
- Reason: 95% success > acceptance threshold (>95% isn't required, ≥95% is)

**Scenario: AC5 spot-checks reveal inconsistencies (architecture accuracy 75% vs. 80% target)**
- Action: Flag in BENCHMARKS-REPORT.md as a finding (not a failure)
- Reason: Benchmarks are validation, not requirements. Report findings honestly.
- Outcome: Informs Phase 4 architecture module review (future task)

**Scenario: GitHub API rate limit hit mid-sampling**
- Action: Cache results so far in `.ases/evidence/repo-list.json`; resume next session
- Reason: Deterministic sampling with seed=42 allows resumption without data loss

---

## Evidence Preservation

If rollback occurs, preserve:
- `.ases/evidence/task-015/` (copy to `task-015-REJECTED/` for reference)
- Any logs showing what went wrong (for root cause analysis)

Do NOT delete if:
- Task is being re-planned (PLANNER revises spec)
- Defect found in Ortho itself (separate bugfix task)

---

## Determinism After Rollback

If task is re-run after rollback:
- Use same sampling seed (42)
- Use same GitHub search query filters
- Results should be identical to previous run
- Allows before/after comparison if a bug was fixed

---

*Rollback version: 1.0 | Created: 2026-07-08*
