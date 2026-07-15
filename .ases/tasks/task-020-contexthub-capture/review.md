# Code Review — task-020-contexthub-capture

**Verdict:** APPROVED (1 real finding, fixed and re-verified during this review)

## Summary
Wires all 4 `CliCommands` methods to real ContextHub capture via a new
`capture_workflow_run` helper. Verified end-to-end against `repos/click`
(4 real `workflow_run` rows via direct sqlite query). A serious
filesystem-contamination bug (unconditional `mkdir` on nonexistent scan
paths) was already found and fixed during BUILDER/TEST-DESIGNER phases.
This review found one additional real issue (below), fixed it, and
re-verified before approving.

## Finding (Fixed During This Review): Live Project Database Pollution
Adversarial check: I ran the full `cli-commands` test suite myself and
then inspected this actual ortho repo's own `.ortho/ortho.db` (not a
tmp_path fixture) directly via sqlite3. Found 4 real `workflow_run` rows
with meaningless content (`"plan: None"`, `"plan: 123"`, `"decide: "`,
`"plan: "`) — genuine pollution of the live project database, written by
`plan()`/`decide()`'s empty/non-str-intent early-return paths, which
called `capture_workflow_run(".", ...)`. Since `"."` resolves relative to
the *caller's* cwd, and pytest's cwd for this suite is the ortho repo
root itself, every test run silently wrote junk rows into ortho's own
real memory store -- the exact opposite of this task's goal (real,
useful engineering memory). `.ortho/` is gitignored, so this wasn't a git
hygiene problem, but it is a real data-quality problem: these rows are
indistinguishable from genuine captured runs once written, and would
accumulate indefinitely across every future test run and every pilot
user's own accidental `plan("")`/`plan(123)` calls.

**Fixed** (this review, not deferred): removed the `capture_workflow_run`
call from both empty/non-str-intent early-return branches in
`plan()`/`decide()`. Rationale: these calls never resolve a real scan
target -- there is no meaningful "repo" to associate the memory with, so
skipping capture entirely is more correct than writing to a fallback
location that happens to be wrong in the common (test/CI) case. Cleaned
up the 4 polluting rows already present in this repo's live
`.ortho/ortho.db` via direct sqlite DELETE (confirmed via `git status
--short .ortho/` that this file is gitignored and the cleanup itself
needed no commit). Updated spec.md with a "Correction (REVIEWER,
post-GATE-5)" note documenting the change. Re-ran the full test suite
post-fix: 100 passed, 1 skipped (unchanged) -- no test depended on the
removed capture calls (confirmed by reading `test_decide_empty_intent_
still_fails_cleanly`, which only asserts `success is False` on the
returned `CliReport`, never asserts a capture row exists for that case).
Re-ran mypy: 27 errors, unchanged (removing a call site doesn't add/
remove type errors here). Re-confirmed the live `.ortho/ortho.db` stays
clean of `workflow_run` rows after the fixed test suite runs.

This is exactly the kind of thing REVIEWER's adversarial, non-mocked
verification exists to catch -- VERIFIER's evidence package (100 passed)
was accurate but didn't surface this, because no test asserted anything
about *this* repo's own database; it only became visible by directly
inspecting the live file this review's own commands happened to be
running against.

## Specification Compliance
✓ `capture_workflow_run`'s signature matches spec.md exactly (API
  Contract Gate, re-confirmed by direct read of all call sites).
✓ Never raises, never flips `report.success` -- verified via
  `TestNeverRaisesNeverFlipsSuccess`'s corrupt-db/malformed-content cases,
  which exercise real failure paths, not mocks.
✓ `get_duplications()`-style empty-signal honesty pattern from task-019
  is not relevant here (different task), but this task follows the same
  "document real gaps, don't fabricate" discipline: content excerpt is a
  plain 2000-char slice with no attempt to summarize/interpret findings.

## Code Quality Assessment
- `workflow_capture.py` is small, single-purpose, and its `is_dir()` guard
  (the BUILDER-phase fix) is exactly the right level of defense -- checked
  before any filesystem-touching object is constructed, with a comment
  explaining why (non-obvious: without the comment, a future editor might
  "simplify" it away, not realizing `OrthoDatabase.__init__` itself has
  the eager side effect).
- `commands.py`'s refactor (build report, capture, return) at every path
  in all 4 methods is repetitive (14 near-identical
  `capture_workflow_run(...); return report` pairs) but this repetition is
  the right tradeoff here: it guarantees no return path can silently skip
  capture in a future edit, which is more valuable than a shared helper
  that could be bypassed. Not flagging as a simplification opportunity.

## Security Assessment
No new input surface. `argument`/`command`/`report.content` all
originate from the same already-validated sources `guardrails()`/
`decide()` already used pre-task-020. No shell invocation, no `eval`.

## Architecture Compliance
✓ Re-verified independently: `cli-commands` (Apps layer, ADR-016) importing
`context-hub`/`shared.storage` (Storage/Shared layers) is explicitly
permitted per ADR-015's Apps row. Confirmed via direct grep of
`workflow_capture.py`'s imports -- no Intelligence-layer or
Engineering-Copilot-layer import.

## Evidence Completeness
✓ Opened `verify_tests_20260715_153144.log` directly: `100 passed, 1
  skipped`, `EXIT_cli-commands:0`.
✓ Opened `verify_mypy_20260715_153144.log` directly: 27 errors, diffed
  against the 23-error clean-master baseline in this review's own
  independent recheck -- confirms net +4, all `import-untyped`.
✓ Directly queried this repo's own live `.ortho/ortho.db` (not evidence-
  log-mediated) -- the source of this review's one real finding.

## Test Authenticity Audit (MANDATORY)
1. **Product imports:** `test_workflow_capture.py` imports real
   `cli_commands.workflow_capture.capture_workflow_run`,
   `context_hub.store.ArtifactStore`, `storage.OrthoDatabase`,
   `repo_intelligence.index_store.mint_repo_id` -- confirmed via direct
   read, not grep alone.
2. **Pass-body / tautology check:** read all 26 test bodies. Every
   assertion depends on either a real `CliReport`/sqlite row/`ArtifactStore`
   return value, or (for the "never raises" class) the mere fact that
   execution reached the assertion line at all after a real failure-
   inducing input (corrupt bytes, whitespace content). No tautologies.
3. **`pytest.raises`:** zero occurrences -- correct, `capture_workflow_run`
   is specified to never raise, so no test should expect it to.
4. **Claimed vs. executed counts:** test-plan.md claims 26 tests (25
   passed + 1 skipped); this review's own `grep -c "def test_"` on
   `test_workflow_capture.py` confirms 26 exactly. No discrepancy.

## Seven Adversarial Questions
1. **What would make this break in production?** Found and fixed in this
   review: writing to a real, unintended `.ortho/ortho.db` when no real
   scan target exists. Also probed: what if two processes capture to the
   same repo concurrently? Out of scope per spec.md (SQLite WAL mode
   provides the same guarantees `guardrails()`/`decide()` already relied
   on; not a regression this task introduces).
2. **What did TEST-DESIGNER not test?** Did not test against the *actual
   ortho repo's own* `.ortho/ortho.db` -- reasonably so, since blind
   TEST-DESIGNER had no way to know `plan("")`'s fallback target was `"."`
   without reading BUILDER's code, which it correctly avoided per shadow-
   parallel discipline. This gap was only catchable by REVIEWER's
   privileged, whole-repo adversarial pass -- which is exactly what
   happened.
3. **What assumption is unverified?** "Callers always pass an explicit,
   real `scan_path`/`path`" -- disproven for the empty/non-str-intent
   case, now fixed by skipping capture there instead of assuming a safe
   fallback location exists.
4. **Dependencies failing?** `ArtifactStore`/`OrthoDatabase` failures are
   caught (verified via corrupt-db test); `mint_repo_id` has no failure
   mode (pure hash function over a path string).
5. **Security surface?** None new.
6. **ADR violations?** None -- independently re-verified.
7. **Evidence complete?** Yes, plus this review's own additional direct
   inspection of the live project database (not reliant on the evidence
   package alone).

## Confidence Level
EVIDENCE-BACKED

## Approval
**Verdict:** APPROVED

**Reason:** One real, non-trivial finding (live database pollution via
an unsafe fallback scan_root) was found, fixed, and re-verified within
this review pass rather than deferred -- unlike task-019's two deferred
findings, this one directly contradicted the task's own stated
correctness goal (real, useful memory) and was cheap to fix immediately
(remove two capture calls, no new files, no test changes needed). Full
test suite and mypy re-confirmed clean post-fix. Combined with the
already-fixed filesystem-contamination bug from BUILDER phase, this task
now has two real capture-safety issues found and fixed across its
lifecycle, which is exactly the "hard test cases that find bugs" outcome
the user asked for.

**Approved by:** REVIEWER
**Date:** 2026-07-15
