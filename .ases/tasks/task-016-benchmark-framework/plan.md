---
title: task-016 — Engineering Benchmark Suite (Modular Framework)
phase: Phase 2 Validation (tooling, parallel to Phase 3/4)
workflow: feature.md
created: 2026-07-09
status: ARCH-APPROVED
---

# task-016: Engineering Benchmark Suite (Modular Framework)

## Purpose

Restructure the existing task-015 benchmark script (`benchmarks/pipeline.py`,
`run_benchmark.py`, `report.py` — a single flat runner) into a modular,
vendor-neutral framework with ground-truth-based correctness metrics
(precision/recall/F1) instead of raw counts. Architected so a second
engineering-agent adapter (Claude Code, Cursor, etc.) could be added later
without touching suite logic — but only the adapter seam is built now, not
the second adapter itself.

## Motivation

task-015 proved the pipeline works end-to-end on 45 real repos (100% success,
Commit e67c3f9) but only reports counts ("38 subsystems", "0.75 confidence")
with no ground truth to check them against, and Ortho's stages are called
directly rather than through a boundary — so it can't be reused to benchmark
anything but Ortho. This task adds the two things task-015 doesn't have:
(1) an adapter boundary so the benchmark engine never touches Ortho internals,
(2) ground-truth comparison so metrics measure correctness, not just output size.

## Scope (7 Atomic Tasks)

**Revised per GATE 2 architecture review (architecture-review.md) — adapter
redesigned capability-based, canonical result model, dataset manifests,
central config, validation layer, and run metadata all incorporated.**

| Task | Deliverable | Owner | Effort |
|------|-------------|-------|--------|
| **AC1:** Core + capability-based adapter | `core/{config,result_model,runner,ground_truth,reports}.py`, `core/metrics/{set_based,ranking,correlation}.py`, `adapters/interface.py` (`EngineeringSystemAdapter`, 5 capability methods), `adapters/ortho/adapter.py` (wraps existing `pipeline.py` stage bodies unchanged, multiple stages collapse into one adapter method) | BUILDER | 3.5h |
| **AC2:** Repository Intelligence suite | `suites/repository/evaluate.py` — precision/recall/F1 for symbols, imports, call graph vs ground truth, returns `SuiteResult` | BUILDER | 2h |
| **AC3:** Architecture suite | `suites/architecture/evaluate.py` — style/layer/subsystem accuracy vs ground truth via `detect_architecture()`, returns `SuiteResult` | BUILDER | 2h |
| **AC4:** Impact suite | `suites/impact/evaluate.py` — precision/recall/F1 vs cached git-history ground truth (authored once into `impact.json`, not recomputed live) | BUILDER | 2h |
| **AC5:** Efficiency suite (Token + Performance) | `suites/efficiency/evaluate.py` — reuses existing timing/memory/context metrics from task-015 pipeline + Compression Ratio; no new correctness dimension (measurement, not accuracy) | BUILDER | 1.5h |
| **AC6:** Retrieval suite + pilot ground truth + manifests | `suites/retrieval/evaluate.py` (Recall@k, Precision@k, MRR, NDCG via `retrieve()`) + hand-authored `datasets/{flask,click}/ground_truth/*.json` + `manifest.json` per dataset | BUILDER | 3h |
| **AC7:** Validation layer | `validation/{test_metrics,test_ground_truth,test_adapter_contract}.py` + `validation/golden/flask_golden.json` + `test_golden_regression.py` | BUILDER + TEST-DESIGNER | 1h |

**Total effort:** ~15h BUILDER + 3.5h TEST-DESIGNER + 1.5h VERIFIER

**Explicitly out of scope (per spec's own "Future Benchmark Suites" section, YAGNI, and GATE 2 review):**
- Robustness suite (broken repos, syntax errors, generated code)
- `adapters/future/` — second vendor adapter (Claude Code, Cursor, etc.) — only the `adapters/ortho/` seam is built; `adapters/interface.py` is designed so a second adapter is addable without touching suite logic, but is not itself built
- Dataset registry / plugin discovery — manual dataset listing is fine at 2 datasets; add a registry only past ~15-20 datasets
- Standalone `cli/` package — one `run_benchmark.py` entrypoint building a `BenchmarkConfig` and invoking `core/runner.py` is enough; no per-suite CLIs
- HTML reports — Markdown + JSON + CSV (task-015's existing format, now rendered from `SuiteResult`) covers current usage; add HTML if/when someone views results outside an editor
- Ground truth for all 45 task-015 repos — 2 pilot repos (flask, click) prove the schema and metrics; scaling ground-truth authoring is a separate future task once the format is validated
- Engineering Task / Agent / Productivity / Change Safety / Cost benchmarks — explicitly deferred by the spec itself; GATE 2 review confirmed the revised (capability-based) architecture supports adding these later without rework

## Key Decisions

1. **Reuse, don't rewrite** — AC1 extracts the existing working task-015 pipeline stages behind an adapter interface; it does not reimplement scanning/architecture/impact logic. task-015's `pipeline.py` stays in place until AC1 lands, then is removed in the same commit that replaces it (rollback-plan covers this).
2. **Ground truth format** — plain JSON files under `datasets/<repo>/ground_truth/{symbols,imports,callgraph,architecture,impact,retrieval}.json`, hand-authored for pilot repos (impact.json authored once from sampled git history, not recomputed live — see architecture-review.md item 3). No schema library — stdlib `json` load + a required-keys/type check in `core/ground_truth.py`.
3. **Metrics modules are generic and grouped by kind** — `core/metrics/{set_based,ranking,correlation}.py` implement precision/recall/F1, Recall@k/MRR/NDCG, and Spearman once each; every suite that needs a metric calls the shared function against its own predicted/expected data. No per-suite metric reimplementation, no flat junk-drawer module.
4. **Adapter interface is capability-based, not stage-based** (GATE 2 change) — `adapters/interface.py` defines `EngineeringSystemAdapter` with exactly 5 methods (`scan_repository`, `detect_architecture`, `retrieve`, `analyze_impact`, `assemble_context`), each phrased as an engineering question rather than an Ortho pipeline stage. `adapters/ortho/adapter.py` implements it by wrapping existing stage bodies, collapsing multiple stages into one method where natural. No abstract base beyond this one interface; no hypothetical vendor-specific hooks added speculatively.
5. **Impact ground truth source** — real git history (files changed together in the same commit) on the pilot repos, authored once into `impact.json` rather than recomputed each run (determinism; matches spec's "Use Git history" instruction while avoiding live-recompute cost/non-determinism).
6. **Canonical result shape** (GATE 2 change) — every suite returns `core.result_model.SuiteResult`; `core/reports.py` is three pure renderer functions (`to_json`, `to_markdown`, `to_csv`) over `list[SuiteResult]`, never suite-specific.
7. **Central config, not per-suite argparse** (GATE 2 change) — `core/config.py`'s `BenchmarkConfig` is built once in `run_benchmark.py` and passed to every suite's `evaluate(adapter, dataset_item, config)`.
8. **Validation is part of Phase 1, not deferred** (GATE 2 change) — `validation/` (golden-output regression, adapter contract test, ground-truth schema checks) ships in this task, not a follow-up, because an untested benchmark produces untrustworthy numbers.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Refactor breaks task-015's working pipeline | Regression in existing benchmark capability | AC1 is a pure extraction (same function bodies, moved + wrapped); VERIFIER re-runs the existing benchmark on 2-3 repos and diffs output against a pre-refactor run to confirm identical metrics; AC7's golden-output test makes this an automated, repeatable check rather than a one-time diff |
| Hand-authored ground truth is wrong/incomplete | False precision/recall numbers | Pilot only (flask, click — both small, well-known repos); TEST-DESIGNER cross-checks a sample of ground-truth entries against actual source before trusting metrics; manifest.json's `commit` pin prevents silent staleness |
| Adapter interface guessed wrong shape for a hypothetical second vendor | Rework when Claude Code/Cursor adapter is actually added | GATE 2 review deliberately re-shaped the interface around capabilities ("what does a benchmark need to ask") rather than Ortho's internal stages, specifically to reduce this risk without building a second adapter now |
| Retrieval suite has no existing precedent in task-015 | Riskiest new code (no reuse baseline) | Keep it deliberately small: stdlib-only Recall@k/MRR/NDCG functions in `core/metrics/ranking.py`, tested against textbook worked examples in `validation/test_metrics.py` before wiring to real data |
| Validation layer adds scope without a working suite to validate yet | Chicken-and-egg: golden output needs a real run first | AC7 ordered last; golden snapshot captured from AC2-AC6's first successful run, not authored speculatively |

## Success Criteria

- [ ] `core/`, `adapters/{interface.py,ortho/}`, `suites/{repository,architecture,impact,efficiency,retrieval}/`, `validation/` exist and each suite runs independently against the `EngineeringSystemAdapter` interface
- [ ] Existing task-015 benchmark capability preserved: re-running on flask/click/requests produces the same counts as before the refactor (verified by AC7's golden-output diff, not just a one-time manual check)
- [ ] Repository + Architecture + Impact suites report precision/recall/F1 against ground truth (not just counts) for the 2 pilot repos, each returning a `SuiteResult`
- [ ] Retrieval suite reports Recall@k, Precision@k, MRR, NDCG against a hand-authored question set for the 2 pilot repos
- [ ] Every suite result renders through the same `core/reports.py` (JSON + Markdown + CSV) — no suite-specific report code
- [ ] Every dataset has a `manifest.json` with commit pin, schema_version, and supported suites list
- [ ] Every `SuiteResult` carries `RunMetadata` (benchmark/dataset/adapter version, timestamp, environment, config used)
- [ ] `validation/test_adapter_contract.py` passes against the Ortho adapter (proves the interface is satisfiable, not just declared)
- [ ] Zero regressions in existing test suites (`pytest` across all packages)

## Definition of Done

- `benchmarks/core/{config,result_model,runner,ground_truth,reports}.py`
- `benchmarks/core/metrics/{set_based,ranking,correlation}.py`
- `benchmarks/adapters/interface.py` + `benchmarks/adapters/ortho/adapter.py`
- `benchmarks/suites/{repository,architecture,impact,efficiency,retrieval}/evaluate.py`
- `benchmarks/datasets/{flask,click}/manifest.json` + `ground_truth/*.json` (pilot ground truth)
- `benchmarks/validation/{test_metrics,test_ground_truth,test_adapter_contract,golden/test_golden_regression}.py` + `validation/golden/flask_golden.json`
- `benchmarks/run_benchmark.py` — thin CLI: args → `BenchmarkConfig` → `core.runner`
- `.ases/evidence/task-016/` — real pytest logs, before/after diff proving AC1 is behavior-preserving
- Old `benchmarks/pipeline.py`, `run_benchmark.py`, `report.py` removed once AC1's replacement is verified equivalent

---

## Architecture Impact

**architecture_impact: LOW** — New package-internal structure (no changes to `packages/*` or shared contracts). GATE 2 review completed; adapter boundary redesigned capability-based, canonical result model, dataset manifests, central config, and validation layer added. See `architecture-review.md`.

→ Full 6-gate workflow, GATE 2 complete

## Next Steps (After GATE 2 Approval)

1. BUILDER implements AC1–AC7 in order (AC1 first — everything else depends on the adapter and core modules existing; AC7 last — golden snapshot needs a real run to capture)
2. TEST-DESIGNER writes tests for metrics/ground-truth/adapter-contract/suites, spot-checks pilot ground truth against real source
3. VERIFIER runs full pytest, diffs refactored pipeline output against pre-refactor baseline on 2-3 repos, confirms golden-output test passes
4. REVIEWER confirms no Ortho internals leak outside `adapters/ortho/` (import-boundary check), ground truth is authentic (not fabricated to make metrics look good), and the adapter contract test genuinely exercises all 5 methods
