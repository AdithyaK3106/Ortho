# Traceability Matrix — task-019-wire-plan-refactor

| Requirement | Architecture | Code | Tests | Evidence | Status |
|---|---|---|---|---|---|
| `plan(intent)` returns real >=3-path FeaturePlan-derived report | architecture-review.md: data flow | commands.py:55-87, feature_plan_adapter.py | test_plan_returns_at_least_3_distinct_paths | verify_tests log | Complete |
| `plan("")` / non-str intent rejected without scan | architecture-review.md | commands.py:57 | test_plan_empty_intent_rejected_without_scan, test_plan_non_string_intent_rejected | verify_tests log | Complete |
| `refactor(path)` returns real bloat + cycle findings | architecture-review.md | refactor_adapter.py, commands.py:89-116 | test_refactor_finds_real_bloat_on_click | verify_tests log; manually verified against repos/click | Complete |
| `get_duplications()`/`get_high_churn_modules()` empty (documented gap) | architecture-review.md "Design Decision Worth Flagging" | refactor_adapter.py:102-106 | test_get_duplications_always_empty, test_get_high_churn_modules_always_empty, test_refactor_no_fabricated_duplication_or_churn | verify_tests log | Complete |
| `refactor(nonexistent)` fails fast | spec.md behavior table | commands.py:92-97 | test_refactor_nonexistent_path_fails_fast | verify_tests log | Complete |
| Existing guardrails()/decide() unchanged (regression guard) | rollback-plan.md | N/A (untouched) | full existing test_commands.py/test_edge_cases_exhaustive.py suite | verify_tests log (72 passed) | Complete |
| mypy --strict introduces zero new type-correctness errors | N/A | feature_plan_adapter.py, refactor_adapter.py | N/A (type-check) | verify_mypy log; git-stash diff in verification-report.md | Complete |
| Real-repo verification (repos/click), bounded/structural assertions | spec.md "Real-Repo Verification Target" | N/A | TestRealRepoRegressionPlanRefactor | verify_tests log | Complete |

## Automatically Detected Gaps

- **Missing implementation:** None.
- **Missing tests:** Minor — self-import cycle handling (REVIEWER Finding
  1) has no explicit test; behavior is a silent drop rather than a crash,
  low real-world impact, deferred to a future task.
- **Missing verification:** None.
- **Missing review:** None — review.md addresses all requirement rows.
- **Orphaned code:** `CodeRepositoryAdapter.self._metrics` (REVIEWER
  Finding 2) is a dead attribute, never read. Deferred (trivial, no
  behavior impact) rather than fixed in this pass, consistent with
  task-018's precedent of documenting non-blocking REVIEWER findings
  rather than reopening an APPROVED verdict for a cosmetic cleanup.
- **Untested implementation:** None at requirement level (see "Missing
  tests" for the sub-case gap).
- **Acceptance criteria without evidence:** None.
- **Evidence without originating requirement:** None.

## Coverage Summary
- Requirements implemented: 8 / 8
- Requirements tested: 8 / 8 (1 minor sub-case gap noted above)
- Requirements verified: 8 / 8
- Requirements reviewed: 8 / 8
