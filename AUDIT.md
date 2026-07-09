# Ortho Repository Audit — pre-GitHub-push

**Date:** 2026-07-09 · **Scope:** whole tree (packages, shared, apps, benchmarks, tests, root, ortho-demo) · **Action taken:** none — report only, nothing deleted.

**TL;DR:** 10,522 files are tracked in git; ~9,770 of them are `venv/` + `node_modules/` and must be untracked before pushing. One mangled-filename log and one stray log are tracked at root. There is no root `README.md` or `LICENSE`. Code-wise: 1 truly dead module, 4 real bugs in `DebtScorer`/`DependencyHealthAnalyzer`, a 4-way duplicated dataclass family, and ~20 stale status-report markdowns at root.

---

## 1. GitHub-push blockers (fix before `git push`)

| # | Problem | Evidence | Fix (when you're ready) |
|---|---------|----------|--------------------------|
| P0-1 | **`venv/` is tracked** — 2,579 files, 57 MB, includes compiled `.pyd` binaries and embedded pip wheels. It's also stale (lacks `tree-sitter`, so this venv can't even run the project). | `git ls-files venv | wc -l` → 2579 | `git rm -r --cached venv` + add `venv/` to `.gitignore` |
| P0-2 | **`node_modules/` is tracked** — 7,193 files, 81 MB, real npm packages (typescript, eslint, babel…). The `.gitignore` comment *"ortho-cli source is tracked under node_modules/"* is a false premise: `node_modules/ortho-cli` is a byte-identical npm `file:`-install **copy** of `apps/cli` (verified with `diff -rq` — no differences). Nothing is lost by ignoring all of node_modules; `npm install` recreates it. | `git ls-files node_modules | wc -l` → 7193 | `git rm -r --cached node_modules` + replace the `node_modules/*/dist/` rule with plain `node_modules/` |
| P0-3 | **Mangled-filename junk file tracked at root:** `"C∶UsersurbraAppDataLocalTempclaude…scratchpadpilot-test.log"` (a Windows temp-path that became a filename, 4 KB pytest log). | `git ls-files | grep pilot-test` (root entry) | `git rm --cached` + delete |
| P0-4 | **`ligence.log` tracked at root** — 10 KB scan log (truncated name of "…intelligence.log"). | root | untrack + add `*.log` (root) to `.gitignore` |
| P0-5 | **No root `README.md`** — GitHub will show the repo with no landing page. `ortho-demo/README.md` exists but the product repo itself has none. | `ls README*` → nothing | write one (the FRD §1–2 + PHASE-1-FINAL-SUMMARY.md are good source material) |
| P0-6 | **No `LICENSE`** at root (`ortho-demo/LICENSE` exists). GitHub flags the repo as unlicensed; nobody can legally use it. | `ls LICENSE*` → nothing | pick a license, copy to root |
| P0-7 | **`apps/cli/src/commands/__pycache__/` exists on disk** inside the TS/py hybrid CLI (untracked thanks to `.gitignore`, but confirms `.pyc` churn in a source dir). | `ls apps/cli/src/commands` | no action needed if P0-2's gitignore stays; just noting |
| P0-8 | **`ortho-demo/` is entirely untracked** (git status `??`). Decide: commit it (it's the demo + dashboard) or push it as a separate repo. Note `ortho-demo/dashboard/data/django.js` is 3.5 MB of generated data — consider regenerating on demand instead of committing, or commit only flask/click data. | `git status` | intentional decision required |
| P0-9 | Secrets scan: **clean.** No `.env`, keys, or credentials in tracked project code (matches found were only stdlib files inside venv/node_modules, which P0-1/2 remove anyway). `ortho-demo/landing` ships only `.env.example` files. ✅ | grep audit | none |

Suggested `.gitignore` additions: `venv/`, `.venv/`, `node_modules/`, `*.log`, `screenshots/` (if you agree with D-7).

---

## 2. Bugs (real defects, with failure scenarios)

### Confirmed

| # | Bug | Location | Failure scenario |
|---|-----|----------|------------------|
| B-1 | **Coupling score saturates at 1.0 for almost every file.** `coupling = min(1.0, (fan_in + fan_out) / 2)` — the docstring says "/(2 × num_files)" but `num_files` is hardcoded `1`. Any file with ≥2 import relationships scores exactly 1.00, which is why every debt hotspot in the dashboard shows "High coupling (1.00)". The metric has no discriminating power. | `packages/impact-analysis/src/impact_analysis/debt_scorer.py:126-135` | flask: 40+ files all "coupling 1.00"; ranking between them is decided by churn alone |
| B-2 | **Churn matched by basename, credits the wrong file.** `path.endswith(file_id.split("/")[-1])` — a commit touching `tests/app.py` counts as churn for `src/flask/app.py` and `src/flask/sansio/app.py` too (any same-named file). Also returns the **first** match instead of the best. | `debt_scorer.py:137-149` | any repo with duplicate basenames (`__init__.py` everywhere!) gets cross-contaminated churn scores |
| B-3 | **Test-coverage score is a constant.** Returns `0.5` for every non-test file ("would need external check in real impl"). It silently contributes a flat +0.10 to every file's debt total while presenting itself as a measured dimension. | `debt_scorer.py:174-183` | two files with identical coupling/churn/complexity always tie, even if one has a full test suite |
| B-4 | **`find_cycles()` accepts `call_graph` and ignores it.** The parameter is documented ("List of CallEdge objects") but never read — cycles are computed from imports only. Callers pass thousands of call edges for nothing. | `packages/impact-analysis/src/impact_analysis/dependency_health.py:122-148` | none functionally; misleading API + wasted argument |
| B-5 | **Risk score saturates for small files.** `risk = min(1.0, (fan_in + fan_out) / (2 × num_symbols))` — a file with 1 symbol and 2 call edges scores 1.0 ("critical"). | `packages/impact-analysis/src/impact_analysis/impact_analyzer.py:75` | dashboard: `docs/conf.py` (0 dependents) shows risk 1.00 while `src/flask/cli.py` (8-file blast radius) shows 0.50 |
| B-6 | **`repo_id` hardcoded in API server.** `repo_id = "repo-default"  # TODO: get from context` — every API caller reads/writes the same repo namespace. | `apps/api_server/src/routers/orchestration.py:126` | two repos analyzed through the API server collide in ContextHub |
| B-7 | **Complexity score is a line-count proxy pretending to be AST depth.** `depth = min(8, max(1, lines // 20))` with a comment admitting "rough heuristic". A 160-line flat config literal scores the same as 160 lines of 8-deep nesting. | `debt_scorer.py:151-172` | complexity dimension adds noise, not signal, to debt ranking |
| B-8 | **`import repo_intelligence` hard-fails without tree-sitter.** `python_adapter.py` raises `ImportError` at import time and `__init__.py` imports it unconditionally — so consumers that only need `ImportGraphBuilder` (no parsing) still can't import the package. This is exactly why the tracked venv can't load the project. | `packages/repo-intelligence/src/repo_intelligence/adapters/python_adapter.py:12-14`, `__init__.py:7` | any environment without tree-sitter can't use *any* part of repo-intelligence |

### Already-documented limitations (keep, they're honest — listed for completeness)

- **Relative imports never resolve** (`from .x import y`) — task-016 finding #1; `ImportGraphBuilder`. Causes flask's `src/flask/` internal imports to resolve 0 times; internal import counts are systematically low; impact recall ~55%.
- **`blast_radius` diverges from dependent counts** — task-016 finding #3; 36–48 files diverge per repo (dashboard `verify_data.py` reports it on every run).
- **Retrieval searches analysis artifacts, not source** — task-016 finding #2; retrieval suite scores ~0 by design, documented in dataset manifests.
- **Subsystem clustering produces one giant cluster on small repos** — flask: 78 of 83 files in one subsystem spanning src+tests+examples. Not wrong per the algorithm, but low-utility output worth a threshold review.

---

## 3. Dead code (ponytail-audit format: `<tag> <what> — <replacement> [path]`)

- `delete:` **`graph_utils.py`** — imported by nothing anywhere (packages, apps, tests, benchmarks). Replacement: nothing. [`packages/arch-intelligence/src/arch_intelligence/graph_utils.py`]
- `delete:` **`call_graph` parameter of `find_cycles()`** — never read (see B-4). Replacement: drop the param, fix 2 call sites. [`packages/impact-analysis/src/impact_analysis/dependency_health.py:122`]
- `yagni:` **4 parallel definitions of `Symbol`/`CallEdge`/`ImportEdge`** — `repo_intelligence` (symbol_extractor.py:14, call_graph.py:22, import_graph.py:13), `arch_intelligence` (arch_detector.py:21-43, its own "type stubs"), `impact_analysis` (types.py:7-31), plus duck-typed `_SymbolRec` in the benchmark adapter. Fields differ slightly between them (task-010 flagged this too). Replacement: one set in `shared/`, or at minimum a comment in each declaring which is canonical. [4 packages]
- `delete:` **root ad-hoc test scripts** — `test_ortho_working.py`, `test_ortho_features.py`, `test_ortho_sample_output.py`, `test_on_real_repos.py` — one-off exploration scripts that duplicate what `benchmarks/` now does properly; not part of any suite (`pytest.ini` doesn't collect them intentionally?). Replacement: nothing, or move under `scripts/` if still used. [repo root]
- `delete:` **`screenshots/`** — 9 dated Windows screenshots (656 KB) from a July 3 debugging session, referenced by nothing. [screenshots/]
- `stdlib:`/`shrink:` nothing significant found in package code — the Python packages themselves are lean (stateless classes, no wrapper layers, no config nobody sets). The heavyweight problems are hygiene, not over-engineering.

### Stale documents at root (move to `docs/archive/` or delete — 20 files, ~230 KB)

Status reports that were "the latest news" once and are now contradicted by later ones: `TASK-001-COMPLETION.md`, `TASK-002-003-COMPLETION.md`, `TASK-002-003-TEST-RESULTS.md`, `TESTING-RESULTS.md`, `TESTING-IMPROVEMENTS.md`, `TESTING.md`, `TEST_RESULTS_INDEX.md`, `QUICK-START-PHASE-2.md`, `PHASE-1-FINAL-SUMMARY.md`, `PRODUCTION-VALIDATION-REPORT.md`, `ORTHO_CAPABILITIES_SUMMARY.md` (already gitignored), `ORTHO_FEATURE_TEST_REPORT.md` (gitignored), `BUG-FIXES-COMPLETE.md`, `BUGS.md` (bugs it lists are marked fixed in commit c1fe239 — verify then archive), `DEPENDENCY-ISSUES.md`, `DOCUMENTATION-INDEX.md` (indexes the files above), `COMPLETE-WALKTHROUGH.md`, `INNOVATION_SUBMISSION.md`, `LANDING_PAGE_REDESIGN.md` + `LANDING_PAGE_SUMMARY.md` (belong in `ortho-demo/` if anywhere), `INTELLIGENCE-IMPROVEMENT-REPORT.md`.

Keep at root: `CLAUDE.md`, `ortho-v3-frd.md`, `ASES_FRD_v1.2.md`, `status.md` (if kept current), `AUDIT.md` (this file, until reviewed).

`.ases/` (7.6 MB, 426 files) is the methodology's evidence trail — legitimately part of the project's story; keeping it is defensible. If repo size matters, the biggest single item inside is a 1.6 MB regression log (`.ases/evidence/task-012/regression-*.log`).

---

## 4. Intentional stubs (fine to ship, but say so in the README)

These are documented design decisions, not bugs — listed so nobody mistakes them for finished features:

- `llm_classify_intent()` returns a canned structure — no live LLM. [`packages/orchestration/src/orchestration/intent/classifier.py`]
- Workflow step execution emits `[stub-llm] no live LLM configured…` as agent output. [`apps/cli/src/commands/workflow_cli.py:56`]
- `SelectorEngine` skill-matching is deliberate Jaccard similarity per ADR-014 ("intentional placeholder", deterministic by spec). [`packages/orchestration/src/selector/engine.py:257`]
- `step_runner.py` still carries "(stubbed; token optimizer task-014)" comments although task-014 landed — comments are stale, code is wired. [`packages/orchestration/src/executor/step_runner.py:23,36`]

---

## 5. Suggested push sequence (after you review/delete)

```bash
# 1. hygiene
git rm -r --cached venv node_modules
git rm --cached "C*pilot-test.log" ligence.log
#    edit .gitignore: add venv/, node_modules/, *.log

# 2. root cleanup per section 3 (your call per file)

# 3. add README.md + LICENSE, decide ortho-demo/ placement

# 4. sanity: full test suite + benchmarks still green
pytest                      # 496 tests
python benchmarks/run_benchmark.py --only flask

# 5. push
```

`net: -9,780 tracked files, -140 MB, -1 dead module, -20 stale docs possible. Package code itself: lean already.`
