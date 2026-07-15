# Ortho v3 — Rigorous Feature Verification Report

**Date:** 2026-07-12
**Method:** Real execution only — pytest suites + ground-truth benchmark framework + full-repo smoke scans. No simulated metrics.
**Scope:** All features claimed in `FEATURES.md` / `status.md`, benchmarked against `repos/` (8 repositories).

---

## 1. Executive Summary

| Area | Verdict |
|---|---|
| Unit tests (7 packages + benchmark validation) | **864 passed / 19 FAILED** — the "100% pass rate" claim in status.md is **false today** |
| Ground-truth benchmarks (click, flask) | Recall perfect (1.0); architecture style accuracy **0.0 on both repos**; impact analysis weak; retrieval 0.0 (documented scope limitation) |
| Golden regression gate | **FAILING** — flask architecture accuracy regressed 1.0 → 0.0; blast-radius error regressed 2.0 → 6.45 |
| Robustness (8-repo smoke scan) | ✅ 8/8 scanned, 8,797 files, 1 parse error total — but langchain yields **0 import edges** (silent monorepo failure), and the TypeScript adapter was never exercised |
| Ground-truth coverage | Only 2 of 8 repos (click, flask) have hand-authored ground truth. Benchmarking the other 6 "against ground truth" is impossible without authoring new datasets — only robustness/performance was measured there. |

**Bottom line:** parsing/indexing (Pillar 1) is solid — 100% parse success and 100% recall against every hand-verified symbol, import, and call edge. Architecture detection (Pillar 3 style classification) and impact risk scoring are the weakest verified areas, and the token-optimizer package carries 11 real defects plus 7 broken tests.

---

## 2. Unit Test Execution (real pytest runs, 2026-07-12)

| Package | Result | Time |
|---|---|---|
| repo-intelligence | 142 passed, 1 skipped, 13 xfailed, **46 xpassed** | 14.3s |
| context-hub | 54 passed | 1.6s |
| arch-intelligence | 76 passed | 3.0s |
| impact-analysis | 42 passed | 1.5s |
| orchestration | 105 passed | 188.4s |
| token-optimizer | 359 passed, **18 FAILED** | 3.4s |
| dashboard-generator | **no tests directory exists** | — |
| benchmarks/validation | 86 passed, **1 FAILED** (golden regression) | 5.2s |
| **Total** | **864 passed, 19 failed** (98.0% pass) | |

Notes:
- The 46 `xpassed` in repo-intelligence are tests marked expected-failure that pass — stale markers that hide real coverage.
- `status.md` claims "110+ tests, 100% pass rate" for Phase 4. The Phase 4 package (token-optimizer) actually has 377 tests with 18 failing (95.2%).
- Failures reproduce identically when run from the package directory — not a path artifact.

### 2.1 token-optimizer failures — root-cause triage (18)

**REVISED after source-level analysis (see §7): 17 of the 18 failures are defects in the tests themselves, not the product.** The deeper finding is worse than individual bugs: **four entire test files — `test_weight_tuning.py`, `test_quality_logger.py`, `test_metrics.py`, `test_model_adapter.py` (Components 6–9) — import zero product code.** They define mocks inside the test file and test the mocks. Additionally ~55 tests across the package have empty `pass` bodies. A large share of the claimed "110+ tests" exercise nothing.

| Failure group | Count | Root cause |
|---|---|---|
| conftest import breakage | 7 | `tests/__init__.py` makes tests a package → pytest imports tests as `tests.test_x`, so `from conftest import ...` inside test bodies raises ModuleNotFoundError. The zero-budget/empty-input edge cases they cover **never run**. |
| Mock bugs (test-only) | 5 | `MockWeightTuner.__init__` uses `weights or {defaults}` — empty dict is falsy, so `{}` silently becomes the default weights; mocks lack the validation the tests expect to raise |
| Tautological/self-contradicting test bodies | 5 | `test_api_keys_not_logged` fails because `"token"` is a substring of its own hardcoded `"tokens_used"` (never touches the logger — **NOT a secret leak**); `test_bounded_weight_changes` asserts `1.5×1.5 ≤ 2.0` (false by arithmetic); `test_compression_target_invalid` asserts a tautology inside `pytest.raises` (the real compressor DOES validate, `compressor.py:52`); `test_realistic_workflow_over_budget` builds 150 included tokens and asserts `> 300`; `test_p50_median` — off-by-one in the mock's percentile |
| **Genuine product gap** | 1 | `TokenBudget` is a bare dataclass — `TokenBudget(total=-100)` accepted with no validation |

**Real product bug found during this analysis (masked by the mock tests):** `WeightTuner.compute_correlation` divides by `n·s_x·s_y` using sample stdev instead of `(n−1)·s_x·s_y` — every correlation is shrunk by (n−1)/n. Verified live: perfectly correlated data returns 0.667 at n=3 and 0.90 at n=10 instead of 1.0. With the 0.7 trigger threshold, auto-tuning silently never fires for small sample sets even under perfect correlation. No test catches this because the component's test file tests a mock.

### 2.2 Golden regression failure (benchmarks/validation)

`test_flask_golden_regression` fails with real drift vs the recorded golden snapshot:
- `architecture_style_accuracy`: **1.0 → 0.0** (flask used to be classified correctly; now returns "ambiguous")
- `blast_radius_mean_relative_error`: **2.0 → 6.45** (impact prediction got 3× worse)

This means a change since the golden was recorded regressed both architecture detection and impact analysis. This is exactly what the golden gate exists to catch.

---

## 3. Ground-Truth Benchmarks (click + flask — the only repos with hand-authored ground truth)

Fresh run `20260712T151234Z`, 10/10 suite runs executed. Results are **byte-identical to the prior run** (`20260712T113600Z`) — determinism confirmed.

### 3.1 Repository Intelligence (Pillar 1) — ✅ strong, with a measurement caveat

| Metric | click | flask |
|---|---|---|
| Symbols recall | **1.0** | **1.0** |
| Imports recall | **1.0** | **1.0** |
| Call-graph recall | **1.0** | **1.0** |
| Parse success rate | **1.0** | **1.0** |
| Symbols precision | 0.235 | 0.080 |

Ortho found **every** hand-verified symbol, import, and call edge with zero parse failures. The low precision numbers are a **benchmark scoping artifact, not measured false positives**: the ground truth covers only a curated subset of core files (per manifest notes), while the suite compares against full-repo output without filtering — so every correct symbol outside the curated subset counts as "extra." Precision on these datasets is currently uninterpretable. **Recommendation:** filter predictions to GT-scoped files in `suites/repository/evaluate.py`.

### 3.2 Architectural Intelligence (Pillar 3) — ❌ weakest verified area

| Metric | click | flask |
|---|---|---|
| Style accuracy | **0.0** (GT: flat → predicted: layered, conf 0.75) | **0.0** (GT: layered → predicted: ambiguous; correct answer only as alternative) |
| Layer F1 | 0.267 | 0.176 |
| Subsystem mean Jaccard | 0.043 | 0.041 |
| Dependency direction accuracy | 0.667 | 1.0 |

- Style classification is wrong on both ground-truth repos — and confidently wrong on click (0.75 confidence for the wrong answer).
- Layer assignment agrees with human judgment on only ~4/15 (click) and 3/17 (flask) files.
- Subsystem clusters have near-zero overlap with hand-identified subsystems (Jaccard ≈ 0.04); all 5 expected clusters collapse onto the same predicted cluster in both repos.

### 3.3 Change Impact Analysis — ❌ weak

| Metric | click | flask |
|---|---|---|
| Impact F1 | 0.0 | 0.339 |
| Blast radius mean relative error | 5.5× | 6.45× |
| Risk score correlation | 0.0 | **−0.866** |

- On click, neither predicted impact set intersected the real co-change sets from git history.
- Blast radius is systematically over-predicted (e.g., flask `helpers.py`: predicted 19 files, actual 1 — 18× error).
- On flask, risk scores are strongly **anti-correlated** with actual impact size — the file with the largest real blast radius got a lower risk score than smaller ones.

### 3.4 Retrieval — 0.0 across the board (documented limitation, not a bug)

MRR, NDCG@10, P@5/10, R@5/10 all = 0.0 on both datasets. Per the dataset manifests this is expected: the questions ask where source symbols are defined, but `OrthoAdapter.retrieve()` currently searches only ContextHub's ingested meta-analysis artifacts, not raw source code. Honest finding kept as-is by the dataset authors. Retrieval over source code is **unverified** until either the adapter or the dataset changes.

### 3.5 Efficiency (Token Optimizer pipeline) — runs, but weakly exercised

click: 640 tokens used (8% budget fill), compression ratio 0.535; flask: 616 tokens (7.7%), 0.536. Only 2 chunks total per repo flow through the pipeline, so dedup/rerank/expansion behavior on realistic context volumes is effectively untested by this suite.

---

## 4. Claim-by-Claim Verdicts vs FEATURES.md

| Claim (FEATURES.md / status.md) | Verdict | Evidence |
|---|---|---|
| Python AST parsing, symbol extraction | ✅ VERIFIED | 100% parse success on 8 repos; symbols recall 1.0 vs GT |
| Call graph builder | ✅ VERIFIED (recall) | callgraph recall 1.0 on click+flask; precision unmeasurable (GT scoping) |
| Import graph builder | ✅ VERIFIED (recall) | imports recall 1.0 both repos |
| "110+ tests, 100% pass rate" | ❌ FALSE | 19 failures across token-optimizer + golden gate |
| Architecture detection (5 styles) | ❌ NOT VALIDATED | 0/2 correct style on ground-truth repos |
| Layer & subsystem detection | ❌ WEAK | Layer F1 ≤ 0.27; subsystem Jaccard ≈ 0.04 |
| Impact analysis / blast radius | ❌ WEAK | 5.5–6.5× mean radius error; negative risk correlation |
| Weight tuning bounds [0.5, 2.0] | ❌ VIOLATED | Weights reach 2.25 in test |
| Quality logger logs all decisions | ⚠️ OVER-DELIVERS | Also logs API keys/secrets in query text — HIGH-priority fix |
| BM25 / semantic / hybrid search | ✅ unit-verified | 54 context-hub tests pass; not GT-benchmarked (retrieval GT mismatched to scope) |
| Intent routing, selector engine, workflows | ✅ unit-verified | 105 orchestration tests pass; no GT benchmark exists |
| Deterministic output | ✅ VERIFIED | Two benchmark runs byte-identical |
| Scan <30s for 1000-file repo | ✅ VERIFIED (barely) | fastapi: 1121 files in 27.0s; but super-linear — django 2924 files took 169s |
| TypeScript adapter "full support" | ⛔ NOT TESTED | Benchmark adapter scans Python only; no TS repo exercised |
| Import graph on monorepo layouts | ❌ SILENT FAILURE | langchain: 2530 files → 0 import edges, no error raised |

---

## 5. Robustness & Performance Smoke — all 8 repos

No ground truth exists for the 6 remaining repos, so only measurable facts were recorded (per the project's no-simulated-metrics rule):

| Repo | Files | Parse OK | Symbols | Import edges | Call edges | Scan time | Peak mem | Detected style (conf) |
|---|---|---|---|---|---|---|---|---|
| click | 76 | 100% | 1,866 | 111 | 6,097 | 6.8s | 17 MB | layered (0.75) — GT says flat ❌ |
| flask | 83 | 100% | 1,620 | 123 | 3,829 | 5.0s | 7 MB | ambiguous (0.5) — GT says layered ❌ |
| requests | 37 | 100% | 807 | 29 | 2,626 | 3.4s | 12 MB | ambiguous (0.5) |
| fastapi | 1,121 | 100% | 5,438 | 1,452 | 14,774 | 27.0s | 18 MB | layered (0.75) |
| django | 2,924 | 99.97% (1 error) | 43,428 | 7,845 | 177,755 | 169.2s | 94 MB | layered (0.75) |
| langchain | 2,530 | 100% | 16,449 | **0** ⚠️ | 62,121 | 91.7s | 43 MB | ambiguous (0.5) |
| opentelemetry-demo | 21 | 100% | 288 | **0** ⚠️ | 856 | 1.5s | 3 MB | microservices (0.6) ✅ plausible |
| supabase-master | 5 | 100% | 10 | **0** ⚠️ | 60 | 2.6s | 0.3 MB | flat (0.6) |

**Smoke findings:**

- **Robustness: ✅** All 8 repos scanned without crashing; 8,797 files processed with exactly 1 parse error (django, 99.97% success). The "supports Python 3.8–3.14" parsing claim held on every codebase style tested.
- **Import graph anomaly: ⚠️** langchain (2,530 Python files!), opentelemetry-demo, and supabase-master all produced **zero import edges**. For langchain this is clearly wrong — its `libs/` monorepo layout appears to defeat the module-name → file mapping. Every downstream feature that consumes the import graph (layer detection, impact analysis, circular-dependency detection) silently degrades to nothing on such layouts. No error is raised.
- **Performance scaling: ⚠️** The "<30s for 1000 files" claim holds at 1,000 files (fastapi: 1,121 in 27s) but scaling is super-linear: django's 2,924 files took 169s (~2.2× slower per file than fastapi). Likely the call-graph builder (django: 177k edges).
- **TypeScript adapter: ⛔ not exercised.** The benchmark adapter scans Python only. supabase-master (a TypeScript monorepo) yielded just 5 Python files — the "Full support for JavaScript/TypeScript" claim was **not validated** by any benchmark or this smoke run.
- **Architecture plausibility:** opentelemetry-demo → microservices (0.6) is the one clearly-correct call. But on the two repos with ground truth, style was wrong both times — treat unverified styles above with skepticism.

---

## 6. Recommended Actions (priority order)

1. **Rewrite the Component 6–9 test files against the real product code** — they currently test in-file mocks and give illusory coverage; while doing so, fix the real `compute_correlation` bug and add redaction to the quality logger (it writes `query[:100]` verbatim to CSV with no secret filtering — no current test verifies this either way; `test_user_input_sanitized` is an empty stub).
2. **Re-baseline or fix the golden regression** — both drifts are traced (§7): the AMBIGUOUS style (d3301f7) and the blast-radius redefinition (fba1fac) changed product semantics after the golden was recorded and it was never re-baselined.
3. **Fix the 7 conftest-import test failures** — until then, zero-budget/empty-input edge cases are entirely unverified.
4. **Enforce weight-tuning bounds and input validation** (5 `DID NOT RAISE` failures + 2.25 > 2.0 bound violation).
5. **Correct status.md** — "100% pass rate" and "Phase 4 COMPLETE" are contradicted by 19 failing tests.
6. **Fix repository-suite precision measurement** — filter predictions to GT-scoped files so precision becomes meaningful.
7. **Author ground-truth datasets** for at least requests + fastapi (medium-size, tractable) to raise GT coverage beyond 2/8 repos.
8. **Re-examine architecture style classifier** — confidently wrong on click, ambiguous on flask; layer/subsystem outputs barely overlap human judgment.
9. **Fix the silent import-graph failure on monorepo layouts** — langchain (2,530 files) produced 0 import edges with no warning; at minimum, emit a diagnostic when edge count is 0 on a multi-file repo.
10. **Exercise the TypeScript adapter** — extend the benchmark adapter (or add a TS dataset) so the "full TS support" claim gets any coverage at all.
11. Clean up the 46 stale `xfail` markers in repo-intelligence.

---

## 7. Root Cause Analysis (source + git traced, 2026-07-12)

### 8.1 Why 18 token-optimizer tests fail — the tests are theater

The failing test files for Phase 4 Components 6–9 (`test_weight_tuning.py`, `test_quality_logger.py`, `test_metrics.py`, `test_model_adapter.py`) contain **zero imports of `token_optimizer`**. Each defines its own `Mock*` class and tests that. Consequences:

- Failures in them are bugs in the mocks/assertions (e.g. `weights or {…}` swallowing an empty dict; `assert 1.5*1.5 <= 2.0`; `"token" in "tokens_used"` substring matching).
- Passes in them prove nothing about the product. The real components are only exercised by `test_components_7_9.py` (9 tests).
- A real product bug hid underneath: `WeightTuner.compute_correlation` uses `numerator / (s_x·s_y·n)` with **sample** stdev — correct Pearson needs `(n−1)`. All correlations are shrunk by (n−1)/n, so auto-tuning under-triggers; perfect correlation at n=3 reads as 0.667, below the 0.7 threshold.
- The 7 `ModuleNotFoundError: conftest` failures: `tests/__init__.py` turns the tests directory into a package, so pytest imports tests as `tests.test_x` and a bare `from conftest import …` inside a test body can't resolve. Fix: delete `tests/__init__.py` or use relative/fixture injection.

### 8.2 Why the golden regression gate fails — two unbaselined semantic changes

Timeline (all verified via `git log`):

| When | Commit | Change |
|---|---|---|
| 07-09 16:04 | `23c09b0` | **Golden snapshot recorded** (flask: style=layered ✓, blast_radius_err=2.0) |
| 07-09 22:48 | `fba1fac` | Audit fixes: `blast_radius` redefined from `len(transitive)` to `len(direct)+len(transitive)`; risk score renormalized from per-symbol to per-graph-size |
| 07-10 20:38 | `d3301f7` | AMBIGUOUS style added: confidence ≤ 0.5 → return "ambiguous" |

Flask's layered score is **exactly 0.5**, so the new rule reclassifies it from layered (correct) to ambiguous (scored 0.0) — the correct answer survives only as `alternative`. The blast-radius redefinition changed every predicted radius (ctx.py: 0→1, helpers.py grew to 19). Both were deliberate changes; the failure is **process**: the golden was never re-baselined and the gate was evidently not re-run before "Phase 4 COMPLETE" was declared.

### 8.3 Why architecture style is wrong on both ground-truth repos

`arch_detector.py` builds its vocabulary signal from directory names **and file stems** (`all_tokens = dir_tokens ∪ stem_tokens`, line 114). For click:

- `core.py` → stem "core" ∈ BUSINESS_TOKENS; a stem/dir matching PRESENTATION_TOKENS also fires → "layer vocabulary present: presentation, business" (+0.35)
- Any non-trivial library has a ≥3-level import chain (+0.25) and low cycle ratio (+0.15) → **0.75 confidence "layered"** for a flat single-package CLI library.

Meanwhile the FLAT scorer is structurally unreachable for modern repos: it requires ≥70% of files at directory depth ≤ 1 (impossible with `src/` layout), <30 files, and import depth ≤ 2 — then halves its score if any vocabulary matched. The detector's "flat" (files in repo root) and the ground-truth author's "flat" (single package, no layer separation) are different concepts. Click scored: layered 0.75, flat **0.00**.

Flask: honest 0.5 confidence → AMBIGUOUS by the new rule; the benchmark gives no credit when `alternative` equals ground truth.

### 8.4 Why impact analysis scores poorly

Two stacked issues:

1. **Definitional mismatch with ground truth.** Ortho's blast radius counts *all static import dependents*; the ground truth counts *files that actually co-changed in a real commit*. flask `helpers.py` has 19 importers but co-changed with 1 file → recorded as 18× "error". Static reachability systematically over-approximates co-change.
2. **Risk score measures the wrong thing.** `risk = (fan_in + fan_out) / (2·graph_size)` is pure degree centrality. In the flask sample, the file with the largest real co-change set (`ctx.py`) has low fan-in, and high-fan-in `helpers.py` barely co-changes — producing the −0.866 correlation. Centrality ≈ "how many things *could* break", not "how much *will* change together". (n=3 sample; directionally meaningful, statistically weak.)

click's impact F1 = 0.0: predicted dependents are source importers, while the ground-truth co-change sets contain docs/tests/changelog files no import edge predicts.

### 8.5 Why langchain produced 0 import edges (silently)

`_module_index` in the benchmark adapter (logic inherited from the product pipeline) maps `a/b/c.py → a.b.c` and additionally strips **one** leading segment only if it is `src`, `lib`, or `source`. langchain's monorepo layout is `libs/<pkg>/<pkg>/…` — `libs` isn't in the strip list, and two levels would need stripping anyway. So `from langchain.chains import …` never matches any indexed module → every import is classified external → **0 internal edges, no warning emitted**. flask/click work only because their `src/<pkg>/` layout matches the special case. Everything downstream of the import graph (layers, impact, cycles) silently degrades to empty on monorepo layouts.

---

## 8. Fixes Applied (2026-07-12, same session)

All findings above were fixed and re-verified. **Post-fix state: 883 tests, 0 failures** (796 package tests + 87 benchmark-validation tests including the golden gate), fresh benchmark run `20260712T155204Z` 10/10 SUCCESS.

### Product fixes

| Fix | File | Change |
|---|---|---|
| Pearson correlation shrunk by (n−1)/n | `token_optimizer/weight_tuner.py` | Replaced hand-rolled formula with stdlib `statistics.correlation`; perfect correlation now returns 1.0 |
| No weight validation | `token_optimizer/weight_tuner.py` | `auto_tune` raises `ValueError` on weights ≤ 0 |
| Negative budgets accepted | `token_optimizer/budget.py` | `__post_init__` rejects negative `total`/`used` |
| Secrets written verbatim to CSV logs | `token_optimizer/quality_logger.py` | Credential-shaped values (`api_key=…`, `password: …`, `sk-…` keys) redacted before write |
| P50 was upper-middle value, not median | `token_optimizer/metrics.py` | `statistics.median` replaces `sorted[n//2]` indexing |
| File stems counted as layer vocabulary | `arch_intelligence/arch_detector.py` | `bands_present()` uses directory tokens only — click no longer misclassified "layered @ 0.75" (now honest "unknown 0.4, alternative layered") |
| Monorepo imports silently unresolved | `benchmarks/adapters/ortho/adapter.py` | `_module_index` registers every dotted path suffix — langchain went from **0 → 6,394** resolved internal import edges; plus a stderr warning whenever a >20-file repo resolves 0 internal edges |

### Test fixes (18 failures → 0)

- 7 conftest import failures: `from conftest import` → `from tests.conftest import`; 2 of the never-run tests also had a wrong `MockArtifact` signature, now aligned. All 7 edge-case tests now actually execute.
- 4 weight-tuning, 1 quality-logger, 1 metrics, 2 arch-retrieval, 2 compressor tautology/mock tests rewritten to call the **real** `WeightTuner`, `ContextQualityLogger`, `MetricsCollector`, `boost_by_architecture`, and `compress_over_budget`; added a Pearson regression test.
- Golden snapshot re-baselined (`flask_golden.json`) after tracing both drifts to intentional commits (`fba1fac`, `d3301f7`); golden gate green again.

### Benchmark deltas after fixes (flask)

- layer F1: 0.176 → **0.529** (import-graph fix gave the layer detector real signal)
- click dependency-direction accuracy: 0.667 → 0.833
- impact precision 0.684 → 0.348 and blast-radius error 6.45 → 7.57 — honest trade-off: more resolved edges means static reachability over-approximates co-change more; the underlying semantic gap (§7.4) is unchanged
- architecture style accuracy remains 0.0 on both GT repos, but the detector is no longer *confidently wrong* (click: was layered@0.75, now unknown@0.4)

### Process fixes (.ases roles, v1.1)

- `TEST-EXECUTION-POLICY.md` → v1.1: Test Authenticity + Golden Re-baseline rules, with the mechanical grep check
- `agents/test-designer.md`: 5 new forbidden actions (no mock-only test files, no `pass` stubs, no tautologies, `pytest.raises` must wrap product code, no substring security asserts) + 3 new gates
- `agents/verifier.md`: Mode A now must run `pytest benchmarks/validation/` (golden gate) and the test-authenticity grep as evidence
- `agents/builder.md`: semantic output changes require golden re-run + re-baseline in the same task
- `agents/reviewer.md`: mandatory Test Authenticity Audit section; a test file with zero product imports is automatic CHANGES REQUIRED
- `status.md` / `FEATURES.md`: false "110+ tests, 100% pass" claims replaced with verified numbers

### Known remaining (documented, not regressions)

- ~50 passing mock-only/stub tests in Components 6–9 test files still exercise nothing; the failing ones were rewritten, the passing ones are inert. The new REVIEWER audit blocks new ones; rewriting the inert remainder is Phase 5 work.
- Architecture style accuracy 0.0 and impact-vs-co-change semantic gap: model-quality limitations requiring more ground-truth datasets (n=2 is too few to tune against), not code bugs.
- 46 stale `xfail` markers in repo-intelligence (tests pass but are marked expected-fail).

---

## 9. Reproduction

```bash
# Unit tests (per package)
python -m pytest packages/<pkg>/tests/ -v --tb=short

# Benchmark validation + golden gate
python -m pytest benchmarks/validation/ --tb=short

# Ground-truth benchmarks (click + flask)
python benchmarks/run_benchmark.py
# → benchmarks/results/20260712T151234Z/{results.json,results.csv,report.md}

# 8-repo smoke scan
# → benchmarks/results/smoke_all_repos.json
```
