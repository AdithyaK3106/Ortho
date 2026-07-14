# Code Review — task-017-repo-graph-queries

**Verdict:** APPROVED (post-fix; see Fix Verification section at end)

## Summary
Builds a real query layer (6 methods across 5 new classes) bridging repo-intelligence's flat edge lists into the protocol shapes change-planner/arch-guardrails require, then wires `ortho guardrails`/`ortho decide` to call the real analysis engines instead of returning hardcoded stub strings. All spec.md acceptance criteria are met and verified against real cloned repos. One moderate error-handling defect found in `repo_scanner.py` blocks APPROVED.

## Specification Compliance
✓ All 6 components implemented per spec.md contracts (verified via independent API Contract Gate: Contract Valid — constructors/methods match spec.md exactly in implementation and tests).
✓ `ArchModelAdapter` correctly constrained to same-package types only (ADR-016 compliance verified — no `repo_intelligence` import in `model_adapter.py`).
✓ `DependencyGraphAdapter` correctly relocated to `cli-commands` (ADR-016 compliance verified — file exists at `packages/cli-commands/src/cli_commands/dependency_graph_adapter.py`, not in `arch-intelligence`).
✓ `plan()`/`refactor()` stubs untouched (files_forbid respected).
✓ Old unconditional stub literals removed (`"No violations found!"`, `"Recommended: Option A"` — confirmed absent via grep, verified independently).

No deviations from the corrected spec.

## Code Quality Assessment
- Readable, consistent with existing project style.
- `path_to_module()` correctly centralized as a single shared helper (spec.md's Notes for BUILDER explicitly required this to avoid disagreeing implementations).
- **Issue found:** see Issue 1 below — over-broad exception handling in the scan loop.

## Security Assessment
- No secrets, no network calls, no new external dependencies.
- Path handling: `scan_repository()` resolves paths but does not sandbox them — a user can point `ortho guardrails` at any filesystem path they already have OS-level read access to. This is pre-existing behavior (`refactor()`/`plan()` stubs already accepted arbitrary paths without restriction) and not a new exposure introduced by this task.
- No injection surface: no shell calls, no string-formatted queries, no `eval`/`exec`.

## Architecture Compliance
✓ ADR-015 (layer boundaries): verified no Intelligence-to-Intelligence import — `model_adapter.py` imports only `arch_intelligence.types`; `dependency_graph_adapter.py` imports `repo_intelligence.import_graph` but lives in `cli-commands` (Apps layer), which ADR-015's table explicitly permits ("Apps: Can import from Core, Intelligence, Storage, Shared").
✓ ADR-016 (Engineering Copilot layer): verified `cli-commands` correctly bridges `change-planner`/`arch-guardrails`/`decision-engine` with real code (`commands.py` imports all three); no Engineering-Copilot-package imports another Engineering-Copilot package's internals directly.

## Evidence Completeness
✓ evidence-package.md shows all gates ✓ through GATE 5.
✓ Opened `.ases/evidence/task-017-repo-graph-queries/mypy_20260714_231609.log` directly: confirmed "Success: no issues found in 5 source files", EXIT:0.
✓ Opened `.ases/evidence/task-017-repo-graph-queries/tests_20260714_231609.log` directly: confirmed all 6 `EXIT_<package>:0` lines present, counts match verification-report.md exactly (176/105/53/37/42/28).
✓ API Contract Gate: Contract Valid, independently re-spot-checked (grep-verified test call patterns against actual `__init__`/method signatures in this review — confirmed match).

## Test Authenticity Audit (MANDATORY)
1. **Product imports:** All 3 new test files import their real product module — `test_graph_queries.py` imports `repo_intelligence.graph_queries.{CodeMetricsAdapter, RepoGraphQueries, SymbolIndex}`; `test_model_adapter.py` imports `arch_intelligence.model_adapter.ArchModelAdapter`; `test_dependency_graph_adapter.py` imports `cli_commands.dependency_graph_adapter.DependencyGraphAdapter`. Verified via `grep "^from\|^import"` — confirmed non-empty, real package imports in all three (not test-local mocks of the unit under test).
2. **Pass-body / tautology check:** Grepped for `def test_.*:\s*\n\s*pass` pattern across all 3 new files — zero matches. Spot-read ~15 individual test bodies — every assertion depends on the return value of a real method call on a real instance (e.g. `queries.find_callers(...)`, `adapter.get_layers()`), not on hardcoded data evaluated without invoking product code.
3. **`pytest.raises` usage:** Zero occurrences in any of the 3 new files (correctly — none of these 5 classes are specified to raise exceptions; graceful degradation via return values is the spec'd contract, e.g. `CodeMetricsAdapter` returns 0 rather than raising on missing/unparseable files).
4. **Claimed vs. executed counts:** test-plan.md claims 68 new/updated cases; verification-report.md's per-package deltas (repo-intelligence +34, arch-intelligence +10, cli-commands +14 new +10 updated existing = 34+10+14+10=68... actually the 10 "updated" cli-commands tests are pre-existing tests modified in place, not new — the log confirms cli-commands went from a documented pre-task baseline of 36 passed to 53 passed post-task, a delta of +17, not +14. This is a minor documentation inconsistency in test-plan.md's arithmetic (not a fabrication — actual executed count in the log is real and higher, not lower, than claimed), noted as Issue 2 below.

## Seven Adversarial Questions

1. **What would make this break in production?**
   `repo_scanner.py`'s three broad `except Exception` blocks (lines 77, 82, 87) would silently convert a real bug (e.g. a future regression in `CallGraphBuilder` raising `AttributeError` on some malformed-but-not-syntax-error input) into "0 edges found for this file," which then silently produces `0 violations` or misses a real `find_callers` result — a false negative in exactly the tool whose entire purpose is catching real problems. No logging, no evidence the failure occurred.

2. **What did TEST-DESIGNER not test?**
   No test exercises `repo_scanner.py`'s exception-swallowing branches directly (e.g. a file that raises `AttributeError` from `CallGraphBuilder`, as opposed to a `SyntaxError`). This is a real coverage gap tied to Issue 1 — the defect and the missing test are the same root cause.

3. **What assumption is this code making that has not been verified?**
   implementation-notes.md's "Honest Assessment" already flags `find_cycles`/`find_callers` as O(V·E)-ish and untested at scale beyond the 3 fixture repos — this is disclosed, not hidden, and acceptable given spec.md's <30s bound was met on the actual specified fixtures.

4. **What happens when dependencies fail?**
   `commands.py`'s top-level `except Exception as e` in both `guardrails()` and `decide()` correctly converts any pipeline failure into `CliReport(success=False)` — this is the right layer for that catch. The problem is one layer deeper, in `repo_scanner.py`, where failures are swallowed before they ever reach that top-level boundary, so `success=True` can be returned even when a per-file analysis silently failed.

5. **What is the security surface of this change?**
   No new surface. See Security Assessment above.

6. **Does this violate any ADR or architecture decision?**
   No. See Architecture Compliance above — verified independently, not just cited from architecture-review.md.

7. **Is the evidence complete or were gates skipped?**
   Complete. All 5 prior gates show ✓. Opened actual log files myself (not relying on Claude's prior summary) — confirmed real.

## Issues Found

### Issue 1: Over-broad exception handling silently swallows non-parse-error bugs
- **Severity:** MEDIUM
- **File:** `packages/cli-commands/src/cli_commands/repo_scanner.py:77,82,87`
- **Problem:** Three `except Exception:`/`except (SyntaxError, Exception):` blocks in the per-file scan loop catch and silently discard *any* exception, not just the expected parse/read failures. Line 77's `except (SyntaxError, Exception)` is additionally dead-weight — `SyntaxError` is already a subclass of `Exception`, so the tuple has no effect beyond `except Exception`. A genuine bug in `CallGraphBuilder`/`ImportGraphBuilder`/`SymbolExtractor` (not a malformed-source parse failure) would be silently absorbed with zero logging, producing a falsely "clean" scan result from a tool whose entire purpose is surfacing real problems.
- **Fix:** Narrow each `except` to the specific expected failure mode (`SyntaxError` for parse failures; drop the redundant `Exception` from line 77's tuple), and add a `logging.warning(...)` call (or equivalent) inside each handler so a real bug is at least visible in logs, matching the pattern already used correctly elsewhere in the codebase (e.g. `repo_intelligence.indexer` logs a warning on indexing errors, as seen in the arch-intelligence benchmark test's captured log output during this same task's verification run).
- **Reference:** spec.md's Notes for BUILDER: "BUILDER must handle file-read/parse errors gracefully (skip + continue, not crash)" — this requires graceful handling of *parse errors specifically*, not blanket exception suppression.

### Issue 2: test-plan.md's cli-commands test-count arithmetic is slightly off
- **Severity:** LOW
- **File:** `.ases/tasks/task-017-repo-graph-queries/test-plan.md` (Deferred section, final paragraph)
- **Problem:** States "34 + 10 + 14 = 68 total new/updated test cases," but cli-commands actually gained 14 new tests (`test_dependency_graph_adapter.py`) plus modifications to existing tests in `test_commands.py`/`test_edge_cases_exhaustive.py`. The log shows cli-commands going from a pre-task baseline (documented elsewhere in this review's evidence chain as 36 passed) to 53 passed post-task — a real, verified, larger-than-claimed improvement, not a fabrication. The stated arithmetic just doesn't cleanly decompose the "10 updated" figure against the log's actual delta.
- **Fix:** Correct test-plan.md's final paragraph to state the actual verified log deltas per package rather than an approximate arithmetic sum, or simply cite the verification-report.md counts directly instead of re-deriving them.
- **Reference:** verification-report.md's own per-package table (already correct) vs. test-plan.md's summary paragraph (imprecise).

## Fix Verification (post-CHANGES-REQUIRED cycle)

Both issues fixed in the same session (narrow BUILDER-only scope, no ARCHITECT/PLANNER rework needed):

- **Issue 1 fixed:** `repo_scanner.py` now catches only `SyntaxError` around `CallGraphBuilder.extract_calls()` (the only call that can actually raise, confirmed by reading `ImportGraphBuilder`/`SymbolExtractor` source — both already swallow all errors internally and return `[]`, so the try/except wrapping them was dead code and has been removed with a comment explaining why). Each handler now logs via `logging.warning(...)` with the real file path and error. Manually verified: a deliberately broken fixture file triggers the warning with the correct path/message, the scan continues, and the broken file's call-graph extraction is skipped while import/symbol extraction (which don't raise) proceed normally.
- **Issue 2 fixed:** test-plan.md's Deferred section now cites verification-report.md's per-package table as authoritative instead of re-deriving an inconsistent sum.
- **New test added:** `test_commands.py::test_guardrails_skips_file_with_syntax_error_without_crashing` — exercises the previously-uncovered branch identified in traceability-matrix.md's gap list.
- **Re-verified:** mypy --strict clean on `repo_scanner.py`. Full regression re-run across all 6 touched packages: repo-intelligence 176/176, arch-intelligence 105/105 (3 pre-existing unrelated deselected), cli-commands 54/54 (+1 from the new test), arch-guardrails 37/37, change-planner 42/42, decision-engine 28/28. Zero regressions.

## Confidence Level
EVIDENCE-BACKED

## Approval
**Verdict:** APPROVED

**Reason:** Both issues from the initial CHANGES REQUIRED pass are fixed and independently re-verified (real manual test of the exception path, full regression re-run, mypy re-run). Spec compliance, architecture compliance (ADR-015/016), security, and test authenticity all remain clean as assessed in the initial pass — the fix cycle touched only the flagged files and did not introduce new scope.

**Approved by:** REVIEWER
**Date:** 2026-07-14
