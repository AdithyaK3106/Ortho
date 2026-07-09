---
title: task-016 — Specification
status: ARCH-APPROVED
---

# task-016 Specification (GATE 2 revised)

Incorporates all 6 required changes from `architecture-review.md`. Supersedes
the GATE-1 version of this file.

## AC1: Core Modules + Capability-Based Adapter

**Given** the existing `benchmarks/pipeline.py` (stage functions: `clone_repo`,
`ortho_init`, `scan_repo`, `build_graphs`, `analyze_impact`,
`assemble_repo_context`) and `benchmarks/report.py` (JSON/CSV/Markdown +
regression),
**when** extracted and redesigned per GATE 2,
**then**:

- `core/config.py` — `BenchmarkConfig` dataclass (`datasets_dir`,
  `output_dir`, `token_budget: int = 8000`, `retrieval_k: tuple = (5, 10)`,
  `only: list[str] | None = None`). Built once in `run_benchmark.py` from
  CLI args, passed to every suite.

- `core/result_model.py` — canonical shapes every suite returns:
  ```python
  @dataclass
  class RunMetadata:
      benchmark_version: str
      dataset_version: str      # manifest schema_version + pinned commit
      adapter_version: str      # ortho_commit(), reusing existing helper
      timestamp: str
      python_version: str
      platform: str
      config: dict

  @dataclass
  class SuiteResult:
      suite: str
      dataset: str
      metrics: dict[str, float]
      detail: dict
      timings: dict[str, float]
      status: str                # SUCCESS | FAILED | PARTIAL
      error: str | None
      run_metadata: RunMetadata
  ```

- `core/runner.py` — vendor-agnostic: `clone_repo`, `PipelineFailure`, the
  `timed()` stage-timing wrapper (all moved unchanged from `pipeline.py`),
  plus one generic loop: `run_suite(suite_module, adapter, dataset_items, config) -> list[SuiteResult]`.

- `adapters/interface.py` — `EngineeringSystemAdapter`, exactly 5 methods:
  `scan_repository(repo_path) -> RepoIndex`,
  `detect_architecture(repo_path) -> ArchResult`,
  `retrieve(repo_path, query, k) -> list[RetrievalHit]`,
  `analyze_impact(repo_path, changed_file) -> ImpactResult`,
  `assemble_context(repo_path, query, budget) -> ContextResult`.
  Each result type is a small dataclass in the same file.

- `adapters/ortho/adapter.py` — `OrthoAdapter(EngineeringSystemAdapter)`.
  Each method's body wraps existing `pipeline.py` functions unchanged:
  `scan_repository` calls `scan_repo` + `build_graphs` internally;
  `detect_architecture` calls `ArchitectureDetector.detect` +
  `LayerDetector.extract_layers` + `SubsystemDetector.detect_subsystems`
  and merges results into one `ArchResult`; `retrieve` extracts the
  existing `_SearchableStore.search` path; `analyze_impact` and
  `assemble_context` wrap `analyze_impact`/`assemble_repo_context` as-is.
  **This is the only file in `benchmarks/` that imports from `packages/*`.**

- `core/ground_truth.py` — `load_manifest(dataset_dir) -> dict`,
  `load_ground_truth(dataset_dir, kind) -> dict`. Validates manifest has
  required keys (`repo`, `commit`, `schema_version`, `suites`) and that
  `kind`'s suite is listed in `manifest["suites"]` before loading; raises
  with a clear message otherwise (no silent empty-dict fallback).

- `core/metrics/set_based.py` — `precision_recall_f1(predicted: set, expected: set) -> dict`,
  `cluster_match(predicted_clusters: list[set], expected_clusters: list[set]) -> dict`
  (best-overlap pairing for subsystem accuracy).

- `core/metrics/ranking.py` — `recall_at_k`, `precision_at_k`, `mrr`, `ndcg_at_k`
  over `list[RetrievalHit]` vs expected file/symbol sets.

- `core/metrics/correlation.py` — `spearman(x: list[float], y: list[float]) -> float`.

- `core/reports.py` — `to_json(results: list[SuiteResult]) -> str`,
  `to_markdown(results: list[SuiteResult]) -> str`,
  `to_csv(results: list[SuiteResult]) -> str`. Pure functions; no suite
  name special-cased.

- Import-boundary rule (enforced by `validation/test_adapter_contract.py`
  or an equivalent check): no file under `core/`, `suites/`, or
  `validation/` imports from `packages/*` — only `adapters/ortho/adapter.py`
  does.

- Running the refactored pipeline against flask/click/requests produces
  metrics identical to the pre-refactor task-015 baseline (VERIFIER diffs
  `SuiteResult.metrics`, excluding `timings` and `run_metadata` which vary
  run-to-run by design).

## AC2: Repository Intelligence Suite

**Given** ground truth `datasets/<repo>/ground_truth/symbols.json`,
`imports.json`, `callgraph.json` (each a JSON array of qualified names /
edge pairs), gated by the dataset's `manifest.json` listing `"repository"`
in `suites`,
**when** `suites/repository/evaluate.py`'s `evaluate(adapter, dataset_item, config) -> SuiteResult`
calls `adapter.scan_repository(repo_path)`,
**then** it computes precision/recall/F1 (via `core/metrics/set_based.py`) for:
- Symbols: predicted qualified names vs ground truth qualified names
- Imports: predicted `(importer, imported)` pairs vs ground truth pairs
- Call graph: predicted `(caller, callee)` pairs vs ground truth pairs

plus Parse Success Rate and Repository Coverage, all in `SuiteResult.metrics`;
per-item Correct/Missed/Extra breakdown goes in `SuiteResult.detail`.

## AC3: Architecture Suite

**Given** ground truth `datasets/<repo>/ground_truth/architecture.json`
(`{"style": "layered", "layers": [...], "subsystems": [[file,...], ...]}`),
**when** `suites/architecture/evaluate.py` calls `adapter.detect_architecture(repo_path)`,
**then** it reports in `SuiteResult.metrics`:
- Architecture Style Accuracy: exact match + confidence score
- Layer Detection Accuracy: precision/recall of (file → layer number) vs ground truth
- Subsystem Detection Accuracy: `core.metrics.set_based.cluster_match()` against
  ground-truth subsystem sets
- Dependency Direction Accuracy: % of ground-truth-labeled layer edges respected

`SuiteResult.detail` carries Ground Truth / Prediction / Correct? / Confidence
per comparison — not a single rolled-up score.

## AC4: Impact Suite

**Given** `datasets/<repo>/ground_truth/impact.json` — authored once (not
computed live) from sampled real commits: each entry is
`{"changed_file": ..., "actually_impacted": [...]}`, derived from the
pilot repo's git history at ground-truth-authoring time and pinned to the
manifest's `commit`,
**when** `suites/impact/evaluate.py` calls `adapter.analyze_impact(repo_path, changed_file)`
for each ground-truth entry,
**then** it computes precision/recall/F1 of predicted-impacted files vs
`actually_impacted`, Blast Radius relative error (predicted count vs actual
count — no separate "accuracy" metric invented beyond this and the
precision/recall/F1 above), and Risk Score Correlation
(`core.metrics.correlation.spearman` between predicted risk score and
`len(actually_impacted)` across all entries — first metric to cut if
time-boxed, per architecture-review.md priority list).

## AC5: Efficiency Suite (Token + Performance)

**Given** the existing `assemble_repo_context` metrics (tokens, latency,
budget fill) and existing timing/memory metrics from `pipeline.py`,
**when** `suites/efficiency/evaluate.py` calls `adapter.assemble_context(repo_path, query, budget)`
and reads the runner's stage timings/memory,
**then** `SuiteResult.metrics` contains two groups: token metrics
(tokens used, budget fill %, Compression Ratio = raw searched tokens /
optimized tokens) and resource metrics (timing per stage, peak memory) —
unchanged from task-015's existing computation, no new ground truth required
(measurement, not correctness — Context Recall/Precision is already covered
by AC6's retrieval suite on the same corpus, not duplicated here).

BUILDER may split this into `suites/token/` + `suites/performance/` instead
of one `suites/efficiency/` if that reads clearer during implementation —
not a hard requirement either way (architecture-review.md, medium priority,
non-blocking).

## AC6: Retrieval Suite + Pilot Ground Truth + Dataset Manifests

**Given** a hand-authored `datasets/<repo>/ground_truth/retrieval.json`:
`[{"question": "...", "expected_files": [...], "expected_symbols": [...]}]`
(≥5 questions per pilot repo),
**when** `suites/retrieval/evaluate.py` calls `adapter.retrieve(repo_path, question, k)`
for each `k` in `config.retrieval_k`,
**then** it computes, per question and averaged: Recall@k, Precision@k
(k=5 and k=10), MRR, NDCG@10 via `core/metrics/ranking.py`, validated
against textbook worked examples in `validation/test_metrics.py` before
running on real data.

**Also in this AC:** `datasets/{flask,click}/manifest.json` authored
(commit pin, `schema_version: 1`, `benchmark_version`, `language: "python"`,
`suites` list, `size_loc`, `ground_truth_authored_by`, `ground_truth_date`)
and `datasets/{flask,click}/ground_truth/impact.json` authored (see AC4).

Ground truth for flask and click is hand-authored by BUILDER, cross-checked
by TEST-DESIGNER against actual source (open the file, confirm the expected
symbol/file is really the right answer) before being trusted.

## AC7: Validation Layer

**Given** the suites and core modules from AC1–AC6,
**when** `validation/` is built,
**then**:
- `validation/test_metrics.py` — worked-example unit tests for every metric
  family (precision/recall/F1 on known sets, NDCG on a known ranking,
  Spearman on known correlated/uncorrelated series)
- `validation/test_ground_truth.py` — manifest schema validation, missing-file
  handling, suite-gating (a suite not listed in `manifest["suites"]` is
  rejected)
- `validation/test_adapter_contract.py` — calls all 5
  `EngineeringSystemAdapter` methods against a small fixture repo (5 files,
  checked into `validation/fixtures/`), asserts each return type matches
  the interface's dataclass contract. This is the executable spec a future
  second adapter must satisfy.
- `validation/golden/flask_golden.json` — one committed `SuiteResult` list
  snapshot from a full flask run, captured after AC2–AC6 first pass
  successfully (not authored speculatively)
- `validation/golden/test_golden_regression.py` — re-runs all suites against
  flask, diffs `metrics` and `detail` fields against the golden snapshot
  (excludes `timings` and `run_metadata`, which vary by design)

## Expected Test Metrics

- **Unit tests:** 28+ (metrics functions across `set_based`/`ranking`/
  `correlation` — worked examples; ground truth loader — missing file,
  malformed JSON, suite-gating)
- **Integration tests:** 10+ (each suite runs end-to-end on 1 pilot repo via
  the adapter, produces a valid `SuiteResult`)
- **Adapter contract tests:** 5+ (one per `EngineeringSystemAdapter` method)
- **Edge cases:** 8+ (empty ground truth, zero predicted items, all-correct,
  all-wrong, k larger than result set)
- **Golden regression:** 1 (flask, full suite run)
- **Regression:** full existing pytest suite across all packages, zero new failures
- **Total:** 52+ tests
- **Expected coverage:** ≥85% on `core/`, `adapters/interface.py`, and
  `suites/*/evaluate.py` scoring logic (adapter methods wrapping existing
  pipeline code inherit task-015's coverage, not re-measured)
- **Expected pass rate:** 100%
- **Known acceptable failures:** None planned. If pilot ground truth
  authoring reveals ambiguous cases, document as `xfail` with reason before
  GATE 4, not after.

## Non-Goals (explicit)

- Not benchmarking any vendor other than Ortho in this task (interface
  supports it later; no second adapter built now)
- Not authoring ground truth beyond flask + click
- Not building a dataset registry or plugin discovery system
- Not building the robustness suite or any Phase-2-listed "future" suite
- Not fingerprinting the full environment (CPU model, installed package
  versions) in `RunMetadata` — `platform.platform()` + Python version only
