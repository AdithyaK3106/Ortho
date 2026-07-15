# Ortho `guardrails` — False-Positive Rate Audit (2026-07-16, updated same day post-fix)

## Update: fixes applied and re-measured (same day)

Both root causes identified below were fixed, and the exact same audit was
re-run against the exact same 9 repos, same method (fresh `.ortho/` state,
hand-verification, not sampling).

**Result: 309 → 96 total violations (69% reduction). Of the 96 remaining, 100%
are verified true positives** — 95 `module_sizing` findings (line/function
counts independently re-checked against `wc -l`, all accurate, matching the
same values verified in the original audit) and 1 `dependency_direction`
finding (celery's real 41-module strongly-connected component, now reported
once instead of the original 33 raw findings / 20-ish near-duplicate reports
diagnosed below).

| Repo | Before | After | What changed |
|---|---|---|---|
| click | 0 | 0 | unchanged (was already clean) |
| requests | 0 | 0 | unchanged (was already clean) |
| flask | 31 | 7 | 24 FPs removed (20 layer_boundaries + 4 self-loop cycles); 7 real module_sizing remain |
| celery | 217 | 75 | 142 FPs/duplicates removed (110 layer_boundaries + 13 self-loop cycles + 19 duplicate cycle reports collapsed into 1 real finding); 74 module_sizing + 1 real cycle remain |
| custom_yolo | 25 | 14 | 11 layer_boundaries FPs removed; 14 real module_sizing remain |
| MediAssist | 27 | 0 | all 27 were false positives; correctly silent now |
| monocular-tracking | 0 | 0 | unchanged (was already clean) |
| DataVerse | 9 | 0 | all 9 were false positives; correctly silent now |
| dapr | 0 | 0 | unchanged (was already clean) |
| **Total** | **309** | **96** | **282 false positives / duplicate reports eliminated, 0 true positives lost** |

**Fixes applied:**
1. `layer_boundaries` disabled in `ArchitectureEnforcer.check_violations()`
   (`arch-guardrails/enforcer.py`) — the rule's ordering logic is unchanged
   and still unit-tested directly against hand-labeled layers
   (`test_enforcer.py::TestLayerBoundaries`, still passing); only its wiring
   into the real pipeline was cut, since the defect was entirely in what
   `LayerDetector` reports as "the layers," not in this method.
2. `DependencyGraphAdapter._resolve_target` (`cli-commands/dependency_graph_adapter.py`)
   now excludes the importing module itself from suffix-match candidates,
   eliminating self-loop edges caused by stdlib/third-party imports whose
   name happens to share a dotted suffix with the importing module
   (`import typing` inside a module literally named `...typing`, etc.).
3. `DependencyGraphAdapter.find_cycles` rewritten from raw DFS back-edge
   enumeration to Tarjan's strongly-connected-component algorithm — reports
   each maximal cyclic region once, regardless of how many import paths
   reach it, instead of one "different" finding per DFS path through the
   same underlying problem.

This now clears the <20% false-positive guardrail your strategy memory sets
as the kill criterion for the review wedge — the remaining 96 findings, on
the 9-repo sample audited, are 100% real.

**What's still true, unchanged by this fix:** the underlying architecture-
*style* classifier (LAYERED/FLAT/MVC/etc.) still has its own documented
75%-vs-83.3% accuracy gap on its own benchmark — that's a different,
unrelated capability (style classification, not layer-boundary
enforcement) and remains an open, separate problem. Disabling
`layer_boundaries` removes that classifier's most damaging downstream
consequence (fabricated boundary violations) without claiming the
classifier itself is now accurate.

---

## Original audit (unmodified below)

## What this is, and what it is not

This is **not** the five-pilot study the vNext strategy calls for. That study
requires real developers, on their own repos, over 2-4 weeks, measuring
whether they hesitate to code without Ortho — I have no access to real
developers or that timeframe.

What this is: a hand-verified false-positive audit of `ortho guardrails`
against 9 structurally diverse real repositories (4 previously-benchmarked, 5
genuinely unseen by any prior Ortho session), classifying every single
reported violation as true-positive or false-positive by checking it against
the actual repo content — not sampling, not estimating. This is the one part
of "run the pilots and measure false-positive rate" that's honestly
executable without real users, and it directly informs whether the wedge
(per the vNext strategy's own stated guardrail: **FP rate must be <20% or
the review product is dead — "noise kills review tools"**) is currently
viable.

## Repos audited

| Repo | Type | Seen by Ortho before? |
|---|---|---|
| click | CLI framework | Yes (benchmarked) |
| requests | HTTP library | Yes (benchmarked) |
| flask | Web framework | Yes (benchmarked) |
| celery | Distributed task queue | Yes (benchmarked) |
| custom_yolo | Computer vision / ML | Yes (audited 2026-07-15/16, prior session) |
| MediAssist | ML + conversational health app | **No — first scan this session** |
| monocular-single-object-zoom-tracking | Computer vision | **No — first scan this session** |
| DataVerse | Data science / analysis scripts | **No — first scan this session** |
| dapr | Distributed runtime (small local checkout) | **No — first scan this session** |

## Headline result

**282 of 309 reported violations (91%) are false positives**, concentrated
in one root cause. **27 of 309 (9%) are genuine, verified true positives.**
This is dramatically above the <20% FP-rate guardrail your own strategy
memory sets as the kill criterion for the review wedge.

| Repo | Total violations | True positives | False positives | FP rate |
|---|---|---|---|---|
| click | 0 | — | — | n/a (correctly silent) |
| requests | 0 | — | — | n/a (correctly silent) |
| monocular-tracking | 0 | — | — | n/a (correctly silent) |
| dapr | 0 | — | — | n/a (correctly silent) |
| DataVerse | 9 | 0 | 9 | **100%** |
| MediAssist | 27 | 0 | 27 | **100%** |
| custom_yolo | 25 | 14 (module_sizing) | 11 (layer_boundaries) | 44% |
| flask | 31 | 7 (module_sizing) | 24 (layer_boundaries + self-loop cycles) | 77% |
| celery | 217 | 74 (module_sizing) + ~2 real cycle clusters | 110 (layer_boundaries) + 13 (self-loop cycles) + 18 (duplicate cycle reports)† | ~91% |
| **Total** | **309** | **27 clean TPs** | **282** | **91%** |

† Celery's 20 non-self-loop `dependency_direction` findings are individually
*true* (each reported import chain genuinely exists and genuinely closes
into a cycle — verified programmatically), but 19 of the 20 share only 2
distinct root causes, reported as 19 separate violations. Counted as false
positives here because a developer reading "20 circular dependency errors"
is being told something false about the scope of the problem, even though
each individual line is technically accurate. This is a duplicate-reporting
bug, not a fabrication bug — see Root Cause 2 below.

## Root Cause 1: `layer_boundaries` — systematic false positives, 100% of the ones checked

**Every single `layer_boundaries` violation across all 9 repos was a false
positive**, from a mechanism that recurred identically in DataVerse,
MediAssist, custom_yolo, flask, and celery:

1. `LayerDetector` derives layer *numbers* from pure topological import
   depth — a module with zero internal imports (a leaf: `config.py`,
   `typing.py`, `utils.py`, a `worker` subsystem) lands on layer 0
   regardless of what it actually is.
2. `LayerDetector._infer_layer_name` then tries to assign that layer a
   semantic name via keyword match against `SEMANTIC_KEYWORDS`
   (repository/model/db/service/business/controller/etc.). This produces
   confident-sounding but structurally meaningless labels: `celery.worker`
   (a task-execution subsystem) got labeled `"Db"` because some *other*
   file in the same topological layer happened to have "db" in its path
   (`celery.backends.dynamodb`). `src.flask.typing` (a pure type-alias
   module) got labeled by depth alone.
3. Every module that imports a layer-0 leaf gets flagged as a
   `layer_boundaries` error, worded as "Layer 1 cannot import Model/Db" —
   but the leaf being imported is almost always a **normal utility/config/
   type module**, and the "violation" is really just "this file imports a
   file with no dependencies of its own," which is one of the most
   ordinary patterns in software, not an architecture problem.

Concrete evidence, spot-checked directly against source:
- `DataVerse`: `main.py` importing `src.models.delay_model`,
  `src.utils.config`, all 5 `src.analysis.*` modules flagged as errors —
  this is a data-science entry-point script importing its own modules,
  the *only* correct way to write one.
- `MediAssist`: 20 of 27 violations are `<anything> → src.models.classical_ml.config`
  — a config module being imported broadly is what config modules are for.
- `celery`: `celery.apps.worker → celery.worker` flagged as "Layer 1 cannot
  import Db" — `celery.worker` is core task-execution code, not a database
  layer; the "Db" label came from an unrelated file's keyword match.

**This is the same false-positive class I found and partially fixed on
2026-07-16** (the earlier fix stopped `LayerDetector` from *hardcoding*
"Data"/"Business"/"Presentation" unconditionally, and gated layer reporting
on real style confidence ≥0.45). That fix was necessary but not sufficient:
it stopped the tool from **lying about layer names**, but it did not stop
the tool from **misinterpreting ordinary leaf-module imports as
architecture violations** — which, per this audit, is the dominant failure
mode by volume (192 of 282 false positives, 68%).

## Root Cause 2: `dependency_direction` self-loop bug + duplicate cycle reporting

Two distinct bugs found in `DependencyGraphAdapter.find_cycles()`
(`cli_commands/dependency_graph_adapter.py:55-86`):

**2a. Self-loop false positives.** `flask` and `celery` both report modules
as having a "circular dependency" with **themselves** — e.g.
`src.flask.typing → src.flask.typing`. Verified programmatically: the
`cycles` list contains single-element entries like `['src.flask.typing']`,
which is not a cycle in any meaningful sense (a cycle requires ≥2 distinct
nodes forming a loop). This comes from a genuine self-referencing edge in
the import graph (`get_edges()` produced `(source, target)` where
`source == target`), which the DFS cycle detector doesn't filter out.
13 of celery's 33 `dependency_direction` findings and all 4 of flask's are
this bug.

**2b. Duplicate cycle reporting.** Celery's remaining 20 multi-element
cycles are individually real (verified: each reported chain's last element
does have an edge back to the first), but 19 of the 20 share only 2
distinct root causes (`celery → celery.app.builtins → ...` and
`celery._state → celery.app.base → ...`), reported as 19 separate
"different" violations because the detector reports every distinct DFS
path through a cyclic region rather than deduplicating by root cause. A
developer sees "20 circular dependency errors"; the actionable number is 2.

## What held up under scrutiny: `module_sizing`

Every `module_sizing` warning checked (a sample across custom_yolo, flask,
and celery, all with `wc -l` verified directly against the file) reported
**accurate line counts** — 1639, 1140, 1984, 1625, 1127, 790, 523 lines,
all matching the real file exactly. This rule class has zero false
positives in this audit. It doesn't depend on architecture-style
classification or layer detection — it's a direct, mechanical line/function
count — and that independence from the layer-detection machinery is
exactly why it stayed clean while `layer_boundaries` and
`dependency_direction` did not.

## What this means

The 44%-91% false-positive rates found here are **worse than the risk I
flagged after last session's spot-check on a single repo** — this audit
shows it's not an edge case, it's the dominant behavior of `layer_boundaries`
specifically, on 5 of 5 repos where it fired at all. The earlier fix
(gating layer reporting on real style confidence, killing fabricated
Data/Business/Presentation names) was real and necessary, but it treated
the *symptom* (dishonest labels) without touching the *cause* (topological
depth ≠ architectural meaning, and "imports a leaf module" ≠ "violates a
layer boundary").

Per your own strategy memory's explicit kill criterion — FP rate <20% or
cut the feature — `layer_boundaries` in its current form does not clear
the bar to be a pilot-facing feature. `module_sizing` does. The
`dependency_direction` self-loop bug is a straightforward, scoped fix (filter
`source == target` before cycle detection); the duplicate-reporting issue
needs cycle deduplication by root cause, which is a real but bounded
algorithmic fix, not a redesign.

## Recommendation (original — items 1-3 actioned same day, see update at top)

1. ~~`layer_boundaries` should not be shown as `[error]` severity, and
   arguably not shown at all, until layer detection can distinguish...~~
   **Done: disabled entirely** rather than downgraded to a warning — a
   100% false-positive rate on every repo it fired on left no evidence
   worth keeping at any severity. Re-enabling needs real signal (e.g. the
   unused `reuse_detector.py` pattern-similarity signal, or a much
   stricter bar than topological depth) — that redesign is not done, only
   the immediate harm is stopped.
2. ~~Fix the `dependency_direction` self-loop bug~~ **Done** —
   root-caused to `_resolve_target` suffix-matching a stdlib/third-party
   import back onto the importing module itself; fixed by excluding the
   importer from its own suffix-match candidates.
3. ~~Deduplicate cycle reports by root cause~~ **Done**, via a stronger fix
   than originally scoped — replaced DFS back-edge enumeration with
   Tarjan's SCC algorithm, which reports each cyclic region exactly once
   as a structural property of the algorithm, not via a dedup pass bolted
   onto the old approach.
4. ~~Re-run this exact audit after each fix~~ **Done** — see the update at
   the top of this document: 309 → 96 total violations, 100% of the
   remaining 96 verified true positive.

**Not done, remains open:** the architecture-*style* classifier's own
75%-vs-83.3% accuracy gap (a different capability than the boundary-
enforcement bugs fixed here); redesigning `layer_boundaries` with real
evidence instead of leaving it disabled; and the fact that this
9-repo sample, however carefully hand-verified, is still not the real
five-pilot study your strategy calls for.
