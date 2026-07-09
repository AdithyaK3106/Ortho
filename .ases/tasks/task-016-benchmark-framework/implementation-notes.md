---
title: task-016 — Implementation Notes (BUILDER)
status: GATE 3 READY
---

# task-016 Implementation Notes

All 7 atomic tasks (AC1–AC7) implemented and committed, each as its own atomic
commit per this repo's process. Old `pipeline.py`/`run_benchmark.py`/`report.py`/
`test_pipeline.py` removed in the same commit that landed AC1's replacement,
per `rollback-plan.md`'s ownership rule.

## Commits

- `be6ab1f` — AC1: core modules + capability-based Ortho adapter
- `6fc928a` — AC2: Repository Intelligence suite
- `966af13` — AC3: Architecture suite
- `c1e724b` — AC4: Impact suite
- `77055db` — AC5: Efficiency suite (Token + Performance)
- `d89c180` — AC6: Retrieval suite + pilot ground truth + dataset manifests
- `23c09b0` — AC7 (BUILDER portion): golden snapshot + efficiency metrics/timings split

TEST-DESIGNER ran in parallel (fresh context, zero access to BUILDER's
in-progress code, per this task's process) and independently authored
`suites/*/test_evaluate.py` and all of `validation/` except the golden
snapshot data file itself — those are TEST-DESIGNER's deliverable and are not
included in the commits above; VERIFIER will find them uncommitted/untracked
alongside this implementation, ready for TEST-DESIGNER to commit separately.

## What Was Built, Per AC

**AC1** — `core/config.py` (`BenchmarkConfig`), `core/result_model.py`
(`SuiteResult`, `RunMetadata`), `core/runner.py` (`clone_repo`,
`PipelineFailure`, `timed()`, `run_suite()` — the first three moved unchanged
from `pipeline.py`), `core/ground_truth.py` (manifest + gated ground-truth
loading), `core/metrics/{set_based,ranking,correlation}.py`, `core/reports.py`
(3 pure renderers), `adapters/interface.py` (`EngineeringSystemAdapter`, 5
capability methods + their result dataclasses), `adapters/ortho/adapter.py`
(`OrthoAdapter` — wraps `pipeline.py`'s `scan_repo`/`build_graphs`/
`ArchitectureDetector`/`LayerDetector`/`SubsystemDetector`/`ImpactAnalyzer`/
`assemble_context`/`_SearchableStore` bodies unchanged, module-level functions
prefixed `_` to mark them as moved-not-rewritten). `run_benchmark.py` rebuilt
as the thin CLI (`BenchmarkConfig` → dataset discovery → `run_suite` per
requested suite → `core.reports` output).

**AC2** — `suites/repository/evaluate.py`: precision/recall/F1 (symbols,
imports, call graph) + Parse Success Rate + Repository Coverage via
`adapter.scan_repository()`.

**AC3** — `suites/architecture/evaluate.py`: style accuracy, layer
precision/recall/F1, `cluster_match()`-based subsystem accuracy, and a new
`_layer_edges_respected()` helper for Dependency Direction Accuracy, via
`adapter.detect_architecture()`.

**AC4** — `suites/impact/evaluate.py`: precision/recall/F1 of predicted vs
actual impacted files, Blast Radius relative error, Spearman risk-score
correlation, via `adapter.analyze_impact()` per ground-truth entry.

**AC5** — `suites/efficiency/evaluate.py`: kept as one module (not split into
token/performance — spec allows either). Reuses `assemble_context()`'s
tokens/budget/chunks plus a derived Compression Ratio, and per-stage timing
around `scan_repository()`/`detect_architecture()`/`assemble_context()`
(+`ingest_analysis_artifacts()` when the adapter exposes it).

**AC6** — `suites/retrieval/evaluate.py`: Recall@k/Precision@k (k=5,10),
MRR, NDCG@10 via `core.metrics.ranking`, calling
`adapter.ingest_analysis_artifacts()` first (mirrors production
`assemble_context()` path) then `adapter.retrieve()` per question. Pilot
ground truth authored for `flask` and `click` — see "Ground Truth Authoring"
below.

**AC7** — TEST-DESIGNER built `validation/{test_metrics,test_ground_truth,
test_adapter_contract,test_import_boundary}.py` and
`validation/golden/test_golden_regression.py` + a `tiny_repo` fixture, all
independently and in parallel. BUILDER's portion: captured
`validation/golden/flask_golden.json` from a real full run (after AC2–AC6
first passed against real flask data, not authored speculatively) and wired
the golden test's `test_flask_golden_regression` body to a real
`run_suite()` call (TEST-DESIGNER had correctly left this as a documented
TODO skip-stub, since they had no completed BUILDER environment to run
against). TEST-DESIGNER subsequently improved that wiring with a
noise-tolerance filter for `peak_memory_mb` — see Known Limitations.

## Ground Truth Authoring (AC6)

Both `flask` and `click` were shallow-cloned (`--depth 1`) into `repos/`
(gitignored) for task-015; for this task both were re-fetched with
`--depth=200` to get real commit history for AC4's impact ground truth.

All ground truth was authored by reading real source directly — grep for
`def`/`class`/import lines, `git log`/`git show --stat` for commit history —
**not** by copying `OrthoAdapter`'s own output, to avoid a circular
"ground truth agrees with the tool because it came from the tool" trap.
Every category was spot-checked against actual source before being trusted
(transcripts of the verification commands are in this session's tool-call
history; summarized per category below):

- **symbols/imports/callgraph.json**: scoped to a curated subset of core
  library files per repo (flask: `config.py`, `helpers.py`, `blueprints.py`,
  `cli.py`, `globals.py`, `signals.py`, `tests/conftest.py`; click: `core.py`,
  `types.py`, `decorators.py`, `exceptions.py`, `globals.py`, `utils.py`,
  `tests/conftest.py`) — not the whole repo, since hand-verifying every
  symbol/import/call across an entire real codebase is not a sound use of
  time at pilot scale. Symbol names verified against `grep -nE "^(def |class
  )"` output; import edges verified against `grep -nE "^(import |from )"`
  plus manual trace of what each import resolves to.
- **architecture.json**: style/layer/subsystem judgment made independently
  by reading source structure (file sizes via `wc -l`, actual import
  relationships), not copied from `ArchitectureDetector`'s own verdict.
  Real finding: flask genuinely has a shallow but real layering (ctx/globals
  core → config/sessions/templating → helpers/blueprints/cli → app); click
  is closer to flat/monolithic (`core.py` alone is 3681 lines, ~30% of the
  package's LOC, holding the entire Command/Option/Context/Group object
  model). `ArchitectureDetector` itself calls both "layered" (0.50 and 0.75
  confidence respectively) — the ground truth deliberately does NOT just
  agree with that; click's style is authored as `"flat"`, so the architecture
  suite's `architecture_style_accuracy` metric on click (`0.0` in the actual
  run) is measuring a real, meaningful disagreement, not a suite bug.
- **impact.json**: sampled from real git history. Flask entries from commits
  `fbb6f0b` ("all teardown callbacks are called despite errors"), `c2705ff`
  ("merge app and request context"), `a29f88c` ("document that headers must
  be set before streaming"); click entries from `051bb0f` ("Do not let the GC
  close a borrowed stdout") and `9f9b149` ("Add @custom_version_option").
  Each commit's real co-changed `.py` files (via `git show --stat`) became
  the `actually_impacted` list.
- **retrieval.json**: ≥6 hand-written questions per repo about real symbol
  locations (e.g. "how do I flash a message to the user" → `flash()` in
  `helpers.py`), each location verified against `grep`.

## Real Findings Surfaced By This Task (not bugs in the benchmark itself)

These are genuine characteristics of Ortho's current pipeline, discovered
while building ground truth and running suites against real data — exactly
what task-016 exists to surface:

1. **Relative imports never resolve internally.** `ImportGraphBuilder`
   extracts the *imported symbol name* for `from .module import Symbol`
   statements (e.g. `AppGroup`, not `.cli`), so `_resolve_import()`'s
   dotted-module-path matching can never resolve a `from .x import y`
   statement to an internal file — only absolute `import module` /
   `from package.module import x` statements resolve. Confirmed on flask:
   123 "internal" import edges, ALL of them from `examples/`/`tests/` doing
   `import flask` or `from flask.globals import ...` — zero from `src/flask/`
   itself, despite `src/flask/blueprints.py` genuinely importing 5 sibling
   modules via `from .x import y`. This is a real, pre-existing
   `repo-intelligence` limitation, not something task-016 introduced or
   should silently work around; ground truth (`imports.json`) was authored
   to reflect what the adapter can *actually* produce today, so the
   repository suite's low import precision/recall numbers are the honest
   measurement, not a suite defect.
2. **`retrieve()` cannot answer source-location questions today.**
   `OrthoAdapter.retrieve()` searches ContextHub's ingested artifacts, which
   (via `ingest_analysis_artifacts()`, mirroring `pipeline.py`'s production
   `_ingest_analysis_artifacts`) are architecture/subsystem/debt *meta-notes*
   about the repo, not raw source code. Retrieval questions asking "where is
   X defined" score ~0 across the board (`mrr=0.0`, `recall_at_5=0.0` on both
   flask and click) — confirmed correct by inspecting the actual ingested
   artifact rows (6–7 meta-analysis notes, no source snippets). Documented in
   both manifests' `ground_truth_notes` rather than "fixed" by injecting
   source code into the retrieval corpus (would violate reuse-don't-rewrite —
   `pipeline.py` never ingested source content either) or rewriting the
   questions to match the tool's current scope (would hide the finding).
3. **`ImpactReport.blast_radius` can diverge from
   `direct_dependents ∪ transitive_dependents`.** Observed on one flask
   sample: `blast_radius=0` while `len(direct_dependents)+len(transitive_
   dependents)=4`. The impact suite reports `blast_radius_rel_error` using
   `ImpactReport.blast_radius` exactly as returned (per spec), so this
   pre-existing `impact_analysis` package characteristic surfaces as a large
   relative error on flask (`2.0`) — a real number, not a suite bug.

## Deviations From Spec

None that change scope or contract. One clarifying extension:
`core.ground_truth.load_ground_truth()` gained an optional `suite=` kwarg
(defaults to `kind`) so several ground-truth files that share one suite's
manifest gate (`symbols.json`/`imports.json`/`callgraph.json` all gating on
`"repository"`) don't require inventing three fake suite names. Spec's
literal signature was `load_ground_truth(dataset_dir, kind)`; this is an
additive, backward-compatible parameter, not a signature change for the
common one-file-per-suite case (`architecture`, `impact`, `retrieval`).

## Known Limitations

1. **`metrics.peak_memory_mb` has natural measurement jitter.**
   `suites/efficiency/evaluate.py` keeps `peak_memory_mb` in `SuiteResult.metrics`
   (not `timings`) per a literal reading of spec.md AC5 ("resource metrics:
   timing per stage, peak memory"), even though — like `context_latency_ms`,
   which IS in `timings` — it varies run-to-run from `tracemalloc`/allocator/GC
   jitter (observed 0.25 → 0.24 → 0.2 MB across three consecutive flask runs
   with zero code changes between them). Rounded to 1 decimal place to reduce
   (not eliminate) false-positive drift. TEST-DESIGNER independently reached
   the same conclusion and added a noise-tolerance filter in
   `test_flask_golden_regression` (filters DRIFT findings on
   `metrics.peak_memory_mb` only, and only when the magnitude is <0.1MB — a
   larger jump, e.g. from a real memory leak, is NOT filtered and still
   fails). This is a real, acknowledged tradeoff between two spec
   requirements (AC5's field grouping vs AC7's strict golden-diff), not an
   oversight; VERIFIER/REVIEWER should treat a recurring small-magnitude
   golden-regression flag on this one field as expected, not a defect.
2. **Ground truth scope is a curated subset, not full-repo, for
   symbols/imports/callgraph.** Documented explicitly in both manifests'
   `ground_truth_notes` and in plan.md's own explicit out-of-scope list
   ("Ground truth for all 45 task-015 repos ... a separate future task").
3. **`impact.json` entries reference commits that predate the manifest's
   pinned `commit`.** Real git history was sampled (shallow clones only had
   1 commit; both repos were re-fetched with `--depth=200` to get usable
   history), and those sampled commits are necessarily older than the
   current `HEAD` used for `manifest.json`'s `commit` pin. File contents may
   have drifted slightly between the sampled commit and the pinned commit;
   the co-change *relationships* are real and verified via `git show
   --stat`, but exact line-level content at the pinned commit was not
   re-verified per entry. Documented in both manifests.

None of the above are `xfail`-marked test failures — they are either
suite-code-level design tradeoffs (peak_memory_mb) or ground-truth-authoring
scope notes (subset coverage, historical commit pinning), not incorrect
implementations of any AC.

## Verification Performed By BUILDER (informal, not a substitute for GATE 5)

- `python benchmarks/run_benchmark.py --only flask,click` → 10/10 suite runs
  SUCCESS across all 5 suites, real cloned repos, real Ortho analysis.
- `python -m pytest benchmarks/` → 135/135 passing (own sanity checks +
  TEST-DESIGNER's independently-written suite), stable across ≥3 repeated
  runs including the golden-regression test.
- `python -m pytest packages/{repo-intelligence,context-hub,arch-intelligence,
  impact-analysis,token-optimizer}/tests/` → zero regressions (142+54+76+42+77
  passing) in every package `OrthoAdapter` touches.
- Import-boundary rule spot-checked manually (only `adapters/ortho/adapter.py`
  imports `packages.*`) and later confirmed by TEST-DESIGNER's
  `validation/test_import_boundary.py` (4/4 passing).

VERIFIER should still run the full Mode A pytest suite with real logs per
CLAUDE.md's Test Execution Policy — the above is BUILDER's own sanity
verification during implementation, not a substitute for GATE 5.
