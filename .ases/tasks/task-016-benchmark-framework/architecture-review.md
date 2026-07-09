---
title: task-016 — Architecture Review
status: APPROVED
gate: 2
---

# task-016 Architecture Review (GATE 2)

**Verdict: APPROVED** — with the 6 required changes below incorporated into
plan.md/spec.md before BUILDER starts. Full critique preserved in session
history; this document is the authoritative record of what changed and why.

## Changes Incorporated

### 1. Adapter interface redesigned: capability-based, not stage-based

**Before:** `OrthoAdapter` mirrored Ortho's internal pipeline stages 1:1
(`scan`, `build_graphs`, `detect_architecture`, `extract_layers`,
`detect_subsystems`, `analyze_impact`, `assemble_context` — 7 methods,
growing with Ortho's internals).

**After:** `adapters/interface.py` defines `EngineeringSystemAdapter` with
exactly 5 methods, phrased as questions a benchmark asks, not steps a
pipeline runs:
- `scan_repository(repo_path) -> RepoIndex` (symbols, imports, calls —
  folds in what was `scan` + `build_graphs`)
- `detect_architecture(repo_path) -> ArchResult` (style, layers, subsystems
  together — folds in what was 3 separate methods)
- `retrieve(repo_path, query, k) -> list[RetrievalHit]`
- `analyze_impact(repo_path, changed_file) -> ImpactResult`
- `assemble_context(repo_path, query, budget) -> ContextResult`

**Why:** A future vendor adapter (Claude Code, Cursor) has no separable
"build_graphs" step — it answers questions about a repo. Stage-shaped
methods would not survive contact with a second adapter; capability-shaped
ones will. `adapters/ortho/adapter.py` implements this by wrapping the
existing `pipeline.py` stage bodies unchanged — multiple stages may collapse
into one adapter method internally. No Ortho pipeline code is rewritten.

### 2. Canonical `SuiteResult` model

**Added** `core/result_model.py`:
```python
@dataclass
class SuiteResult:
    suite: str
    dataset: str
    metrics: dict[str, float]
    detail: dict            # per-item correct/missed/extra for drill-down
    timings: dict[str, float]
    status: str              # SUCCESS | FAILED | PARTIAL
    error: str | None
    run_metadata: "RunMetadata"   # see item 6
```
`core/reports.py` becomes three pure functions — `to_json`, `to_markdown`,
`to_csv` — each taking `list[SuiteResult]`. No suite-specific report code;
no suite imports `core/reports.py` directly.

### 3. Dataset manifest

**Added** `datasets/<repo>/manifest.json` per dataset:
```json
{
  "repo": "flask",
  "url": "https://github.com/pallets/flask",
  "commit": "<pinned-sha>",
  "language": "python",
  "schema_version": 1,
  "benchmark_version": "0.1.0",
  "suites": ["repository", "architecture", "retrieval", "impact"],
  "size_loc": 12000,
  "ground_truth_authored_by": "human",
  "ground_truth_date": "2026-07-09"
}
```
`core/ground_truth.py` reads this before loading any ground-truth file;
rejects a suite run if the dataset's `suites` list doesn't include it
(fail loud, not silent-empty). `commit` pins ground truth to a specific
snapshot so authored data doesn't silently go stale as the pilot repos move.

### 4. Central `BenchmarkConfig`

**Added** `core/config.py`:
```python
@dataclass
class BenchmarkConfig:
    datasets_dir: Path
    output_dir: Path
    token_budget: int = 8000
    retrieval_k: tuple[int, ...] = (5, 10)
    only: list[str] | None = None   # dataset name filter
```
One dataclass, built once from CLI args in `run_benchmark.py`, passed to
every suite's `evaluate(adapter, dataset_item, config)`. Replaces per-suite
argparse.

### 5. Validation layer

**Added** `validation/`:
- `test_metrics.py` — worked-example unit tests for every metric family
  (set-based, ranking, correlation) — already planned in AC1/AC6, now
  explicitly homed here rather than scattered
- `test_ground_truth.py` — schema validation, missing-file handling,
  manifest `suites` gating
- `test_adapter_contract.py` — every `EngineeringSystemAdapter` method
  called against a 5-file fixture repo, asserts return shape — this is
  the executable spec a future second adapter must satisfy
- `golden/flask_golden.json` + `test_golden_regression.py` — one committed
  `SuiteResult` snapshot for flask, diffed each CI run (excluding
  timings/machine-dependent fields) to catch benchmark-itself regressions,
  not just Ortho regressions

**Why:** GATE-1 spec had no validation section at all. A benchmark that
isn't itself tested produces untrustworthy numbers — this was the single
largest gap in the original proposal.

### 6. Run-level reproducibility metadata

**Added** `RunMetadata` (part of `core/result_model.py`, not a separate
module — folds into item 2's canonical shape rather than adding new
plumbing):
```python
@dataclass
class RunMetadata:
    benchmark_version: str    # git-describe or VERSION file in benchmarks/
    dataset_version: str      # manifest.json schema_version + commit, joined
    adapter_version: str      # ortho_commit (existing helper in run_benchmark.py, reused)
    timestamp: str
    python_version: str
    platform: str              # sys.platform
    config: dict                # BenchmarkConfig, serialized
```
Populated once per run in `run_benchmark.py` (reusing the existing
`ortho_commit()` helper from the current `run_benchmark.py` — no new git
plumbing needed), attached to every `SuiteResult` in that run. Machine info
kept to `platform.platform()` + Python version — stdlib only, no new
dependency, no attempt at exhaustive environment fingerprinting (CPU model,
installed packages, etc. — YAGNI until reproducibility issues actually
require it).

## Explicitly Not Changed

- Reuse-over-rewrite for AC1 (wrapping existing `pipeline.py` bodies)
- Pilot-only ground truth (flask, click)
- Suite selection (6 suites; Token+Performance merge into Efficiency is
  BUILDER's discretion, not mandatory)
- Out-of-scope suites (robustness, agent comparison, etc.) remain deferred

## Updated Effort Estimate

~14h BUILDER (adapter redesign is roughly a wash vs. original; AC7
validation adds ~1h, largely test infra already budgeted under
TEST-DESIGNER) + 3.5h TEST-DESIGNER + 1.5h VERIFIER.

## Next Step

plan.md and spec.md updated to reflect these 6 changes (see diffs). BUILDER
proceeds to GATE 3 implementing the revised AC1–AC7.
