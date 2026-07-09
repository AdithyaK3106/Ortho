# Ortho Intelligence Improvement Report

**Date:** 2026-07-08
**Scope:** Architecture style detection, subsystem detection, semantic intent routing — quality pass before public-repo benchmarks. No new features, no API breaks, no schema changes.
**Regression status:** 455 tests passing, 0 failing (repo-intelligence 142, context-hub 54, arch-intelligence 76, impact-analysis 42, orchestration 105, apps/cli 30 + 6 jest). The orchestration count *rose* from 93 to 105: the 12 model-dependent intent-router tests that had been skipped since task-012 now execute and pass.

---

## 1. Architecture Detection Improvement Report

**What was wrong:** every scorer was a placeholder. `_score_microservices` returned 0.9 for any repo with ≥15 unique caller symbols, so every real-world repository classified as "microservices 0.90" regardless of structure.

**What replaced it:** evidence-driven scoring in `arch_detector.py`. Each style is scored from independent, generic signals; every fired signal emits a human-readable evidence line; competing scores are always reported; below a 0.45 evidence threshold the detector returns **UNKNOWN** instead of guessing (`ArchStyle.UNKNOWN` added — additive enum change, string value `"unknown"` already used by the CLI for unindexed repos).

Signals per style (all ecosystem conventions, none repository-specific):

| Style | Signals |
|---|---|
| layered | layer vocabulary bands (presentation/business/data) in dirs+stems · import-DAG depth ≥3 (Kahn peeling, stdlib) · low import-cycle ratio · downward cross-band import flow |
| mvc | complete model/view/controller triad · MVC framework imports (django, flask, …) · view/controller→model import flow · acyclic roles |
| hexagonal | ports+adapters vocabulary · isolated core/domain · observed dependency inversion (adapter→core imports, zero core→adapter) |
| microservices | ≥3 sizeable top-level components (one generic level of monorepo-container expansion) · per-component entry points (main/app/wsgi/… stems) · import-independence (<5% cross-component imports) · messaging/RPC dependencies (grpc, kafka, celery, …) |
| flat | shallow file tree · no architectural vocabulary (vocabulary presence is an explicit counter-evidence penalty) · shallow import chains · small size |

**Results on real repositories:**

| | Before | After |
|---|---|---|
| FastAPI | microservices **0.90** (evidence: none real) | **layered 0.75** — "Layer vocabulary present: presentation, data", "Import graph forms 8-level dependency chain", "Low import-cycle ratio (0.0%)"; competing: microservices 0.45, mvc 0.35, hexagonal 0.00, flat 0.00 |
| LangChain | microservices **0.90** | **layered 0.50** — all three layer bands present; competing: microservices 0.45 explicitly flagged as plausible alternative (honest for a monorepo of layered libraries) |

Empty/insufficient input now yields UNKNOWN with an explanation (verified by updated unit tests); a 4-file synthetic "services/" fixture that the old detector force-classified now correctly returns UNKNOWN (0.40, strongest candidate reported).

---

## 2. Subsystem Detection Improvement Report

**What was wrong:** Louvain ran directly on the file-level call graph. Since ~90% of dynamic calls are dropped as unresolved (ADR-011 "never guess"), the graph was so sparse that nearly every file became a singleton community.

**What replaced it:** multi-signal **package-graph** clustering in `subsystem_detector.py`. Files always belong to their package (directory); packages are clustered over a composite weighted graph:

- internal import edges between packages — weight 1.0
- call edges between packages (via symbol→file mapping) — weight 0.5
- parent/child namespace hierarchy affinity — weight 0.25

Louvain (`seed=42`, sorted iteration, stable IDs) clusters packages; each community's files form one subsystem. Subsystems are named after their dominant package (common-prefix naming produced six clusters all called "Docs Src"). API preserved: `detect_subsystems(call_graph, symbols, files)` unchanged; `import_graph` added as an optional keyword argument (additive).

**Results:**

| Metric | FastAPI before | FastAPI after | LangChain before | LangChain after |
|---|---|---|---|---|
| Subsystems | 978 | **21** | 1733 | **38** |
| Avg size (files) | 1.1 | **53.4** | 1.5 | **66.6** |
| Singletons | ~87% | **0** | ~85% | **3** |
| Avg coupling | n/a (degenerate) | 0.66 | n/a | 0.12 |
| Avg cohesion (1−coupling) | — | 0.34 | — | 0.88 |
| Deterministic across runs | yes | **yes (verified)** | yes | **yes (verified)** |

Example subsystems now read as logical components: `fastapi/middleware`, `docs src/security`, `libs/core/langchain core/tracers`, `libs/langchain/langchain classic/document loaders`.

---

## 3. Intent Router Integration Report

**What changed:** the temporary keyword bridge in `workflow_cli.py` is now the *fallback*; the primary path is the task-012 `IntentRouter` (semantic-router + `BAAI/bge-small-en-v1.5`), exactly as designed.

Work required to make the existing implementation actually run:

1. **Dependencies installed** (`transformers`, `torch`) — the router had never executed; its 12 tests were skipped for lack of the model. (`semantic-router[local]` itself fails to install on this machine because `llama-cpp-python` needs a C toolchain; the two libraries the encoder needs were installed directly.)
2. **API compatibility with installed semantic-router 0.1.2** (`router.py`): `HuggingFaceEncoder(name=…)` (was `model=`), `SemanticRouter` from `semantic_router.routers` with `auto_sync="local"`, classification via `router(text)` → `RouteChoice` (the `.classify()` method never existed in this version).
3. **Score semantics fixed:** default `aggregation="mean"` dilutes scores by a route's *other* utterances — an exact corpus match scored 0.67–0.80 depending on corpus density, unpredictably crossing the 0.7 threshold. `aggregation="max"` makes confidence the best single-utterance similarity, which is what the class's documented contract ("raw semantic similarity score") always claimed. Exact matches now score ~1.0. Root-caused by probing two router instances with different corpora (no state bleed; pure aggregation artifact).
4. **Utterance corpus added** (`orchestration/intent/corpus.py`): hand-authored generic developer phrasing keyed by the workflow intent classes the SelectorEngine consumes (documented task-012 limitation until real usage logs exist).
5. **Threshold (0.7) and the task-014 LLM fallback stub are unchanged.** When semantic confidence < 0.7 the router still reports `llm_fallback`; the CLI bridge then uses keyword classification for planning rather than the stub's placeholder answer.

**Routing results (deterministic across repeated calls, verified):**

| Input | Intent | Confidence | Method |
|---|---|---|---|
| "what is the impact of changing the routing module" | analysis | 0.83 | router |
| "write an ADR for the storage decision" | architecture_review | 1.00 | router |
| "fix the crash in the login flow" | bug_fix | — | keyword fallback (semantic 0.56 < 0.7) |
| "bake a chocolate cake" | analysis (default) | 0.50 | keyword fallback |

---

## 4. Benchmark Comparison (before → after)

| | FastAPI | LangChain |
|---|---|---|
| Architecture style | microservices 0.90 → **layered 0.75** | microservices 0.90 → **layered 0.50 (microservices 0.45 flagged)** |
| Evidence lines | 2 generic → 4–5 concrete, signal-level | 2 generic → 4–5 concrete |
| Competing scores exposed | no → **yes, all five styles** | no → **yes** |
| Subsystems | 978 → **21** | 1733 → **38** |
| Avg subsystem size | 1.1 → **53.4 files** | 1.5 → **66.6 files** |
| Singleton clusters | ~850 → **0** | ~1470 → **3** |
| Intent routing | keyword only → **semantic (bge-small), confidence exposed, keyword fallback** | same |
| Full pipeline (scan→analyze→impact→context→workflow) | ✅ completes | ✅ completes |
| Regression suites | 443 passing → **455 passing** (12 formerly-skipped router tests now run) | — |

---

## 5. Remaining Limitations

1. **`ortho run` pays ~70–85 s of model-load time per invocation** on this machine (torch import + bge-small init; only `run` classifies — status/history/approve are unaffected). Mitigation candidates: a lighter embedding backend or a persistent process; both are out of scope here.
2. **Off-topic input** ("bake a cake") falls through semantic (correctly no route) and keyword (no match) to the default `analysis` class instead of being refused. A "none of the above" refusal is a behavior change left for the task-014 LLM fallback.
3. **FastAPI's core package clusters with `tests/`** (723-file subsystem): tests import the core heavily and Louvain merges them. Evidence-driven and defensible, but "tests vs production code" separation may be desirable for benchmarks.
4. **LangChain's layered verdict is near-threshold (0.50 vs micro 0.45)** — genuinely ambiguous for a monorepo of libraries; the competing score is surfaced rather than hidden. UNKNOWN on similar repos is possible and intended.
5. **Deployment/communication signals are limited to Python evidence** (external imports). The scan only indexes `.py` files, so docker-compose/k8s manifests are invisible to the microservices scorer until the indexer widens.
6. **Utterance corpus is hand-authored** (8 utterances/class); routing quality on unusual phrasing depends on it. Documented task-012 limitation until real usage logs exist.
