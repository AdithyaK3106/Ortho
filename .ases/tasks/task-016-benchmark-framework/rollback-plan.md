---
title: task-016 — Rollback Plan
status: PLANNED
---

# task-016 Rollback Plan

## Local (not yet committed)

If BUILDER's work is incomplete or wrong before any commit lands:
`git checkout -- benchmarks/` restores the pre-task state (existing
`pipeline.py`/`run_benchmark.py`/`report.py` untouched). Since `benchmarks/`
is currently untracked (per `git status`), this task's first commit is also
the first time `benchmarks/` enters git history — see "First commit" below.

## First commit (benchmarks/ currently untracked)

`benchmarks/` does not appear in git history yet (task-015 produced it but
never committed the directory — only `.ases/` artifacts and results were
referenced). This task's AC1 commit will be the first to add `benchmarks/`
to git. Rollback for this specific step: `git rm -r --cached benchmarks/`
un-stages without deleting working files, since nothing is being overwritten
that git already tracks.

## Published (after commit)

Each atomic task (AC1–AC6) is its own commit. If a later AC is wrong:
`git revert <commit-sha>` for that AC's commit only — earlier ACs (and the
adapter boundary they depend on) are unaffected since each suite is
independent once AC1 lands.

If AC1 itself (the adapter extraction) is wrong — e.g. VERIFIER's
before/after diff shows the refactored pipeline no longer matches
task-015's original output — revert AC1's commit, which restores
`pipeline.py`/`run_benchmark.py`/`report.py` to their working task-015
state, and no downstream AC (which all depend on the adapter existing)
should have been merged yet.

## Trigger Conditions

- VERIFIER's before/after diff (AC1) shows metric drift beyond timing/memory
  noise → revert AC1, do not proceed to AC2–AC6
- Pilot ground truth (AC6) found to be wrong after TEST-DESIGNER cross-check
  → fix the ground truth JSON directly (data fix, not a code revert)
- A suite's scoring logic produces nonsensical results on the worked-example
  validation (e.g. NDCG suite doesn't return 1.0 for a perfect single-doc
  case) → block that AC's merge, do not revert others

## Ownership

Old `pipeline.py`/`run_benchmark.py`/`report.py` are deleted in the same
commit that lands AC1's replacement (`core/` + `adapters/ortho/`) — no
parallel dead code left behind. If rollback is needed after that commit,
`git revert` restores the deleted files along with removing the new ones,
in one step.
