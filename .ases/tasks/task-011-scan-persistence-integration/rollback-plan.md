# task-011: Scan Persistence + Integration — Rollback Plan

**Format:** Compact (FRD Part 17)

## Triggers

- Any AC fails at GATE 5 and root cause is architectural (not a fixable bug)
- Regression in any existing suite that cannot be fixed within the task
- Migration 002 corrupts an existing `.ortho/ortho.db` (data loss in artifacts table)
- REVIEWER verdict CHANGES-REQUIRED twice on the same structural issue

## Procedure

**Published commits (pushed):** `git revert <sha>` per atomic-task commit, newest first
(5 commits max, each task = one commit, so reverts are surgical).

**Local only (not pushed):** `git reset --hard <last-good-sha>` where last-good is the
commit before Task 1's commit.

**Database artifacts:** `.ortho/ortho.db` is generated state, never source of truth —
rollback = delete `.ortho/ortho.db` and re-run `ortho scan` on the reverted code.
Exception: artifacts table may hold user-ingested content. Before running migration 002
on a DB with >0 artifacts rows, VERIFIER's integration test proves copy-fidelity
(row counts + content hashes identical pre/post). If migration 002 must be rolled back on
a real DB: restore from the `.ortho/ortho.db.bak` the migration test requires (migration 002
itself performs rename-based rebuild, so the pre-migration table survives as `artifacts_old`
until the copy is verified — drop only after count match).

## Order of Reverts (dependencies)

1. Task 5 commit (end-to-end tests) — no dependents
2. Task 4 commit (context CLI) — depends on 3
3. Task 2 commit (scan wiring) — depends on 1
4. Task 3 commit (migration 002) — after 4 is gone
5. Task 1 commit (IndexStore) — last

## Verification After Rollback

- All 7 suites green at the reverted SHA (same counts as pre-task baseline:
  85+46xp / 54 / 76 / 42 / 37 / 16+6 / 7)
- `tsc --noEmit` exit 0
- `ortho scan` on fixture exits 0 (back to non-persisting behavior, no crash)
- `ortho analyze` returns the "not indexed" guard message on a fresh repo
