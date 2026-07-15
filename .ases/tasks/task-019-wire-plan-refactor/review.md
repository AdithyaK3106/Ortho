# Code Review — task-019-wire-plan-refactor

**Verdict:** APPROVED (with 2 minor non-blocking findings)

## Summary
Wires `CliCommands.plan()`/`.refactor()` to real `feature-planner`/
`refactoring-advisor` engines, replacing 100%-hardcoded stub output.
Matches spec.md's contract exactly (verified independently in the API
Contract Gate). Real bloat detection confirmed against `repos/click`.
Deliberately empty `get_duplications()`/`get_high_churn_modules()` is an
honest, documented gap rather than fabricated data.

## Specification Compliance
✓ `plan()`/`refactor()` signatures unchanged aside from `refactor`'s
  `path: str = None` -> `path: str | None = None` (a real mypy fix, not
  scope creep — same function this task modifies).
✓ Both new adapters match spec.md's documented constructor/method shapes
  exactly (Contract Valid, re-verified independently in this review via
  direct read of both adapter files against spec.md's tables).
✓ Empty/non-str intent rejected before any scan (verified: reading
  `commands.py:57`, `if not intent or not isinstance(intent, str)`).
✓ `get_duplications()`/`get_high_churn_modules()` return `[]`
  unconditionally — confirmed by direct read, matches the documented
  non-goal.

## Code Quality Assessment — Findings

### Finding 1 (Minor, non-blocking): Self-import cycles silently dropped
`refactor_adapter.py`'s `get_tight_couplings()` (line 74:
`len(cycle) == 3 and cycle[0] == cycle[-1]`) and `get_circular_deps()`
(line 85: `len(cycle) > 3 or (len(cycle) == 3 and cycle[0] != cycle[-1])`)
both implicitly assume `find_cycles()` never returns a length-2 chain.
Verified adversarially (this review): a module that imports itself
(`from . import selfimp` referring to its own module) produces a real
`['a', 'a']` cycle from `DependencyHealthAnalyzer.find_cycles()`, which
satisfies neither classification's length condition and is silently
dropped — a genuine self-referential circular import produces zero
findings from `refactor()`, when it arguably should surface as
`circular_deps` (a self-import is a degenerate 1-node cycle, a real code
smell). Low real-world impact (self-imports are rare, usually a mistake
caught by `import.py`'s own `ImportError` at runtime rather than an
architectural issue), and not a regression — the old stub never
detected any real issues at all. Worth a follow-up task if this file is
touched again; not blocking for this task's stated scope (bridge two
already-existing engines to real cli-commands data, not build a fully
exhaustive cycle taxonomy).

### Finding 2 (Trivial, non-blocking): Dead attribute
`CodeRepositoryAdapter.__init__` sets `self._metrics = None  # set lazily
to avoid import cycle at module load` (refactor_adapter.py:35), but
`get_bloated_modules()` (line 90-92) constructs its own local `metrics`
variable instead of ever reading or writing `self._metrics`. The
attribute is entirely dead code — a leftover from an earlier draft.
Harmless (no behavior impact, confirmed by reading every reference to
`self._metrics` in the file: there are none besides the assignment
itself), but should be deleted for clarity in a future pass.

Neither finding blocks approval: both are pre-existing-class minor gaps
(narrow edge case; dead code), not defects in the task's stated
behavior, and both are far smaller in scope/impact than the two real
bugs already found and fixed during BUILDER/TEST-DESIGNER phases (the
non-str-intent crash, the pre-existing test-hang defect).

## Security Assessment
No new input surface beyond what `guardrails()`/`decide()` already
established (real filesystem scan of a user-provided path). No shell
invocation, no `eval`/`exec`, confirmed by reading both new adapter files
in full.

## Architecture Compliance
✓ Re-verified independently (not just citing architecture-review.md):
`grep -rn "^from\|^import" packages/cli-commands/src/cli_commands/
feature_plan_adapter.py packages/cli-commands/src/cli_commands/
refactor_adapter.py` shows only `arch_intelligence.types`,
`impact_analysis.*`, `cli_commands.repo_scanner` — no
Intelligence-to-Intelligence import, matches ADR-015/016.

## Evidence Completeness
✓ Opened `verify_tests_20260715_131151.log` directly: `72 passed`,
`EXIT_cli-commands:0`.
✓ Opened `verify_mypy_20260715_131151.log` directly: 23 errors, diffed
against clean-master baseline (22) in this review's own independent
`git stash` comparison — confirms net +1, zero new type-correctness
errors from new code, one baseline error (`implicit Optional` on
`refactor()`) fixed.
✓ Confirmed zero modification to `feature-planner`/`refactoring-advisor`/
`impact-analysis` source (`git status` shows no changes under those
package directories).

## Test Authenticity Audit (MANDATORY)
1. **Product imports:** `test_plan_refactor_wiring.py` imports real
   `cli_commands.feature_plan_adapter.FeaturePlannerArchModelAdapter`,
   `cli_commands.refactor_adapter.CodeRepositoryAdapter`,
   `cli_commands.repo_scanner.scan_repository` — confirmed via direct
   read, not grep alone.
2. **Pass-body / tautology check:** read all 17 new test bodies plus the
   3 modified pre-existing tests. Every assertion depends on real
   `CliCommands`/adapter output; `test_get_bloated_modules_matches_real_
   thresholds` in particular loops over the *actual* returned tuples and
   asserts each individually exceeds the threshold, rather than
   asserting a fixed count — correctly avoids overfitting.
3. **`pytest.raises`:** zero occurrences — correct, since none of the new
   public methods are specified to raise (they return `success=False`
   reports instead).
4. **Claimed vs. executed counts:** test-plan.md claims 17 new tests in
   the new file; this review's own count of `test_plan_refactor_wiring.py`
   test methods (`grep -c "def test_"`) confirms exactly 17. No
   discrepancy.

## Seven Adversarial Questions
1. **What would make this break in production?** Probed (this review):
   self-import cycles (Finding 1). A module with thousands of imports
   would work but be slow (`get_bloated_modules` reads every file's
   source twice per module for lines+functions — O(n) file I/O, matches
   `guardrails()`'s existing pattern, not a new performance class).
2. **What did TEST-DESIGNER not test?** Self-import cycle handling
   (Finding 1) — not in the 17-test suite. Minor gap, matches the
   severity of the finding itself.
3. **What assumption is unverified?** "`find_cycles()` never returns a
   length-2 chain" — disproven in this review (Finding 1), but low
   impact.
4. **Dependencies failing?** N/A — pure computation over already-scanned
   in-memory data, no new I/O beyond file reads already present in
   `scan_repository()`/`CodeMetricsAdapter`.
5. **Security surface?** None new (see Security Assessment).
6. **ADR violations?** None — independently re-verified via grep.
7. **Evidence complete?** Yes — both logs opened and spot-checked
   directly in this review.

## Confidence Level
EVIDENCE-BACKED

## Approval
**Verdict:** APPROVED

**Reason:** Matches spec.md exactly, real bloat/coupling detection
verified against `repos/click`, zero regressions, two genuine bugs found
and fixed during the task's own build/test phases (non-str-intent crash,
pre-existing test-hang defect). The two findings in this review (dropped
self-import cycles, one dead attribute) are minor, non-blocking, and
smaller in scope than what the task already caught and fixed on its own
— they are follow-up material, not grounds to send this back.

**Approved by:** REVIEWER
**Date:** 2026-07-15
