# Traceability Matrix — task-020-contexthub-capture

| Requirement | Architecture | Code | Tests | Evidence | Status |
|---|---|---|---|---|---|
| All 4 commands capture a real workflow_run artifact after every call | architecture-review.md | commands.py (14 call sites), workflow_capture.py | TestArtifactIsRealAndQueryable, TestMultipleRunsProduceSeparateArtifacts | verify_tests log; manual repos/click sqlite check | Complete |
| Capture never raises, never flips report.success | architecture-review.md "Failure Isolation Review" | workflow_capture.py try/except | TestNeverRaisesNeverFlipsSuccess (6 tests incl. corrupt db, malformed content) | verify_tests log | Complete |
| Two different repos yield two different, stable repo_ids | spec.md "repo_id Resolution" | workflow_capture.py: mint_repo_id(resolved_root) | TestRepoIdStabilityAndUniqueness (4 tests) | verify_tests log | Complete |
| Existing guardrails/decide/plan/refactor behavior unchanged | rollback-plan.md | commands.py (report built before capture call) | TestExistingCommandBehaviorUnaffectedByCapture (7 tests) | verify_tests log | Complete |
| Content excerpt bounded (~2000 chars) | spec.md "Content Format" | workflow_capture.py: content[:_CONTENT_EXCERPT_CHARS] | TestContentExcerptBounding (3 tests) | verify_tests log | Complete |
| mypy --strict introduces zero new type-correctness errors | N/A | workflow_capture.py | N/A (type-check) | verify_mypy log; git-stash diff (23->27, all import-untyped) | Complete |
| Real-repo verification (repos/click): 4 rows in .ortho/ortho.db | spec.md "Real-Repo Verification Target" | N/A | test_running_all_four_commands_against_click_yields_four_rows | verify_tests log; manual sqlite query | Complete |
| No unsafe fallback scan_root pollutes an unrelated real database | REVIEWER finding (review.md) | commands.py: empty/non-str-intent paths skip capture entirely | Existing empty-intent tests confirm success=False unaffected | review.md; manual live .ortho/ortho.db inspection (0 rows post-fix) | Complete (fixed during REVIEWER) |

## Automatically Detected Gaps

- **Missing implementation:** None.
- **Missing tests:** None blocking. The live-database-pollution finding
  was, by nature, not testable via `tmp_path` fixtures (it required
  inspecting the actual project repo's own `.ortho/ortho.db`) -- correctly
  caught by REVIEWER's privileged whole-repo pass rather than TEST-
  DESIGNER's necessarily-sandboxed tests. No further test needed since the
  fix (skip capture for those 2 early returns) makes the failure mode
  structurally impossible rather than merely detected.
- **Missing verification:** None.
- **Missing review:** None.
- **Orphaned code:** None.
- **Untested implementation:** None.
- **Acceptance criteria without evidence:** None.
- **Evidence without originating requirement:** None.

## Coverage Summary
- Requirements implemented: 8 / 8
- Requirements tested: 8 / 8
- Requirements verified: 8 / 8
- Requirements reviewed: 8 / 8
