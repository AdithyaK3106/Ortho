# Ortho vNext — Delta Implementation Blueprint

**Type:** Delta document against the current codebase (verified 2026-07-16), not a
from-scratch design. Every "exists" / "partial" / "missing" claim below was checked
against real source files, not inferred. File:line references are given so this
document can be re-verified in one pass.

**Why a delta, not a fresh FRD:** ~45% of the requested Pillars 1, 3, and part of 4
already exist and work, including the exact illustrative example the source document
uses for Engineering Memory ("this recommendation was made before on X during
workflow #N"). Designing those from scratch would either duplicate working,
tested code or silently regress a bug fix shipped two days before this document
was requested (the false-positive layer-naming fix — see Pillar 1). This document
tells you what to keep untouched, what to extend, and what is genuinely greenfield.

---

## 0. Scorecard

| Pillar | Status | Real completion |
|---|---|---|
| 1. Repository-Aware Engineering Review | Core loop built, FP-rate work already shipped | ~60% |
| 2. Evidence Engine | Field exists, unpopulated; no structured model | ~15% |
| 3. Engineering Memory | Citation loop built and verified end-to-end | ~50% |
| 4. Engineering Intelligence | Impact analysis + architecture detection real; debt intelligence partial | ~35% |
| 5. Repository Understanding (Q&A) | Nothing built | 0% |
| Single-command unification | Two commands (`guardrails`, `decide`) do most of the loop separately | ~40% |

---

## Phase 1 — Product Architecture (delta)

### 1.1 Module boundaries — mostly correct already, one addition needed

Current package layout (ADR-015/ADR-016 already enforce this; do not restructure it):

```
repo-intelligence   → call graph, import graph, symbol extraction (WHAT exists)
arch-intelligence   → architecture style, layers, subsystems (WHAT IT MEANS, structurally)
context-hub         → artifact storage, BM25 search, memory substrate
change-planner      → impact prediction (blast radius)
arch-guardrails     → violation rules (layer_boundaries, dependency_direction, module_sizing)
decision-engine     → multi-source recommendation aggregation
feature-planner     → intent → implementation-path suggestions
refactoring-advisor → bloat/coupling/cycle findings
cli-commands        → orchestration layer (Apps, per ADR-016) — wires all of the above
                       into guardrails()/decide()/plan()/refactor()/search_memory()
```

**This already matches the source document's module-boundary intent.** Repository
Intelligence tells you what exists; Architecture/Engineering Intelligence tells you
what it means; `cli-commands` is the orchestration layer that assembles one report
from many packages. Do not add a new top-level "Engineering Intelligence" package —
that's what `cli-commands` + `arch-guardrails` + `decision-engine` already are,
combined.

**One real gap:** there is no `evidence` package. Evidence today is an untyped
`list[str]` field bolted onto `GuardrailViolation` (`arch-guardrails/types.py:11`)
and `Recommendation` (`decision-engine/types.py:13`), populated inconsistently.
Phase 2 below specifies a real `Evidence` model; it should live in a new
`packages/evidence` package that both `arch-guardrails` and `decision-engine`
depend on (one-way, per ADR-015 — evidence is a lower layer, never imports
guardrails/decision types back).

### 1.2 Data flow — already close to the target diagram

Current, verified flow for `guardrails()` (`cli-commands/commands.py:136-199`):

```
scan_repository(path)                     [repo-intelligence + arch-intelligence]
  → ArchitectureDetector.detect(...)      [real style + confidence, wired 2026-07-16]
  → LayerDetector.extract_layers(...)     [only populates layers if style implies a
                                            real hierarchy at >=0.45 confidence]
  → ArchitectureEnforcer.check_violations()
  → cite_prior_findings(...)              [queries workflow_run history BEFORE this
                                            run's own capture — memory citation]
  → capture_workflow_run(...)             [this run becomes tomorrow's memory]
  → CliReport
```

This is already the "Repository Intelligence → Architecture Intelligence → Evidence
→ Memory Retrieval → Report → Memory Update" loop from the source document's
diagram, minus one stage (Impact Analysis is only invoked in `decide()` today, not
`guardrails()`) and minus real structured Evidence. Both are additive changes to
this existing pipeline, not a redesign of it.

### 1.3 Public interfaces — extend, do not replace

`CliCommands` (`cli-commands/commands.py`) is the correct single orchestration
class. The delta:

- Add `CliCommands.review(path_or_intent, **kwargs) -> CliReport` — the unified
  single command the source document asks for. Internally it should call the same
  scan + enforcer + predictor + citation pipeline `guardrails()`/`decide()` already
  call, just merged into one report instead of split across two commands users
  have to know to call separately.
- `guardrails()`/`decide()` remain as-is underneath `review()` (or become thin
  wrappers around it) — do not deprecate them; MCP tool names and existing tests
  depend on them.

---

## Phase 2 — Storage Models (delta)

### 2.1 What exists and should NOT change

`context_hub.schema.init_artifact_schema` (`context-hub/schema.py:8-28`) — the
`artifacts` table with FTS5 BM25 search is the correct, working memory substrate.
`Artifact` (`context-hub/store.py:23-39`) already has `id, repo_id, type, title,
content, source, created_at, tags, related_symbols, estimated_tokens,
content_hash, version`. This is a reasonable generic artifact model. **Keep it.**
Do not build a parallel "memory" table — `workflow_run` is already just an
`artifact.type` value; new memory kinds (rejected recommendations, incidents)
should be new `type` values in the same table, not new schemas.

### 2.2 New: Evidence model (genuinely missing — build this)

```python
# packages/evidence/src/evidence/types.py (new package)

@dataclass(frozen=True)
class EvidenceRef:
    """One piece of evidence backing a finding. Immutable, content-addressed."""
    id: str                    # stable hash of (source, locator, snapshot) — reproducible
    source: EvidenceSource      # enum: SYMBOL_GRAPH | IMPORT_GRAPH | ARCH_MODEL |
                                 #       WORKFLOW_HISTORY | ADR | GIT_HISTORY
    locator: str                # e.g. "file:models/model.py#L42", "artifact:abc123",
                                 #      "adr:ADR-015"
    summary: str                 # one-line human-readable ("imported by 17 files")
    confidence: float            # 0.0-1.0, source-specific (graph facts = 1.0,
                                  #   BM25-matched history = relevance_score)

@dataclass(frozen=True)
class EvidencedFinding:
    """A finding that must trace to >=1 EvidenceRef. No finding without evidence
    is constructible -- this is the type-level enforcement of the source
    document's 'never make claims without evidence' requirement."""
    claim: str                        # "violates dependency direction"
    evidence: tuple[EvidenceRef, ...]  # non-empty, enforced in __post_init__
    confidence: float                  # aggregate, never higher than min(evidence confidences)

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("EvidencedFinding requires at least one EvidenceRef")
```

**Why a new package, not a field on existing types:** the source document is
explicit that "unknown" must be preferable to guessing, and that every conclusion
needs evidence. Making that a *type-level* invariant (you cannot construct an
`EvidencedFinding` without evidence) is the only way to guarantee it — a
convention ("please populate the evidence list") is exactly what already failed
silently (evidence fields exist today and are mostly empty). `GuardrailViolation`
and `Recommendation` should each grow an `evidence: tuple[EvidenceRef, ...]`
field replacing today's `list[str]`, populated at the point each is constructed
in `enforcer.py`/`decision_engine/engine.py`.

### 2.3 Extend: workflow_run artifact content (small, additive)

Today `capture_workflow_run` (`workflow_capture.py:23-65`) stores `content =
f"success={report.success}\n\n{report.content[:2000]}"` — free text. Add
structured fields to the ingestion so citation queries (2.4) don't depend on
BM25-over-prose matching a `rule_id location` string against report text:

```python
# ArtifactIngestionRequest gains an optional structured_refs field:
structured_refs: list[dict] = field(default_factory=list)
# e.g. [{"rule_id": "layer_boundaries", "location": "models.model -> utils"}]
```

This is additive to `context_hub.ingestion.ArtifactIngestionRequest` — does not
change the `artifacts` table schema, stored as a JSON column alongside `tags`.
Improves citation precision without a migration.

### 2.4 Accept/reject state (missing — needed for "rejected recommendations" memory)

The source document wants memory of *rejected* recommendations specifically.
Nothing in the current codebase captures accept/reject at all — every
`workflow_run` is just "this ran," not "the developer acted on this." New,
minimal addition:

```python
@dataclass(frozen=True)
class RecommendationOutcome:
    workflow_run_artifact_id: str
    recommendation_title: str
    outcome: Literal["accepted", "rejected", "unknown"]
    reason: Optional[str] = None   # free text, e.g. "caused circular deps" — this
                                     # is what makes "ADR-15 rejected this because
                                     # of circular dependencies" possible
    recorded_at: str
```

Requires a new CLI surface (`ortho feedback <workflow_id> accept|reject
[--reason]`) — this is the one piece of genuinely new user-facing interaction in
the whole document, and it's small.

---

## Phase 3 — Pipelines (delta)

### 3.1 Review pipeline — extend `guardrails()`, don't rebuild it

Already exists, already fixed for the FP-rate requirement. Delta:
1. Populate `EvidenceRef`s at each violation site in `enforcer.py` instead of
   the current unused `evidence: list[str]`.
2. Call `ChangePredictor.predict_impact()` unconditionally (today gated behind
   `is_file_intent` in `decide()` only — `commands.py:242-252`) so blast radius
   appears in every review, not just file-path-intent `decide()` calls.
3. Merge into the new `review()` entry point (Phase 1.3).

### 3.2 Repository Intelligence pipeline — unchanged

`scan_repository()` (`repo_scanner.py:48-`) is correct and complete for Python.
No delta.

### 3.3 Evidence pipeline — new, small

A pure function, not a service: `collect_evidence(violation_or_recommendation,
scan: ScanResult) -> tuple[EvidenceRef, ...]`. Looks up the graph facts
(`RepoGraphQueries.find_importers` already gives "imported by 17 files" —
`repo_intelligence/graph_queries.py:63` — this is a direct, already-built
evidence source, just not yet packaged as `EvidenceRef`s) plus a
`cite_prior_findings`-style memory lookup.

### 3.4 Memory pipeline — extend `cite_prior_findings`, don't replace it

Verified working end-to-end (first run: no citation; second run: cites first;
cross-command citation confirmed). Delta: switch its BM25 query from prose
matching to matching against `structured_refs` (2.3) for higher precision, and
add a query against `RecommendationOutcome` (2.4) so "this was rejected before"
becomes constructible, not just "this was mentioned before."

### 3.5 Impact pipeline — unchanged, just called more often

`ChangePredictor.predict_impact()` exists, works, is under-invoked (3.1.2).

### 3.6 Architecture pipeline — unchanged, recently hardened

`ArchitectureDetector` + `LayerDetector` — the false-positive fix already
shipped (see Pillar 1 in the scorecard) is exactly this document's Priority #1
requirement, already done. No further delta beyond wiring `EvidenceRef`s into
its output (3.1.1).

### 3.7 Repository Q&A pipeline — genuinely new, scope it narrow

This is the one pillar with zero existing code. Do **not** build general NL
Q&A in v1 (see Phase 5 priority ordering — this is explicitly deprioritized).
When built, it should NOT be vector-similarity RAG (the source document is
right to reject that) — it should be a constrained query planner over the
existing graph primitives (`RepoGraphQueries.find_callers`/`find_importers`,
`SubsystemDetector`), translating a fixed small set of question shapes ("how
does X reach Y", "what owns X") into graph traversals, not open-ended NL
generation grounded in embeddings. This is real, scoped R&D — budget it as
such, not as "add a chat box."

---

## Phase 4 — API / CLI / MCP Design (delta)

### 4.1 CLI — one addition, no breaking changes

```
ortho review [path|intent] [--severity] [--confidence]   # NEW — unifies
                                                            # guardrails+decide+impact
ortho guardrails [path]           # unchanged, kept for backward compat
ortho decide <intent>             # unchanged, kept for backward compat
ortho plan <intent>               # unchanged
ortho refactor [path]             # unchanged
ortho memory search <query>       # unchanged
ortho feedback <workflow_id> accept|reject [--reason]   # NEW — Phase 2.4
```

### 4.2 MCP tools — one addition to the existing five

Current tools, verified (`apps/mcp-server/ortho_mcp_server.py:63-165`):
`ortho_guardrails`, `ortho_decide`, `ortho_plan`, `ortho_refactor`,
`ortho_memory_search`. Add `ortho_review` wrapping the new unified command.
Do not remove the other five — Claude Code agents may already be calling them
by name in existing pilot sessions.

### 4.3 Response schema — extend `CliReport`, add typed fields

```python
# cli_commands/types.py — additive fields, nothing removed
@dataclass
class CliReport:
    title: str
    content: str
    format: str = "text"
    success: bool = True
    violations: Optional[Any] = None
    recommendations: Optional[Any] = None
    search_results: Optional[Any] = None
    evidence: Optional[list["EvidenceRef"]] = None      # NEW
    impact: Optional["ImpactPrediction"] = None          # NEW — currently only
                                                           # reachable via decide()
    memory_citations: Optional[list[str]] = None          # NEW — currently
                                                           # inlined into .content
                                                           # as text; also expose
                                                           # structured for MCP
```

### 4.4 Streaming / caching / incremental updates — not needed yet, say so plainly

The source document asks for these under Phase 4. Being honest: nothing in the
current usage pattern (single-repo, local SQLite, sub-2s scans on real repos
verified this week) needs streaming or a cache layer. `scan_repository()` is
already fast enough that adding response streaming would be solving a
performance problem that doesn't exist yet, at the cost of real complexity
(partial-result consistency, MCP streaming protocol support). **Do not build
this in the next 12-18 months** unless a pilot user hits an actual latency
wall on a specific large repo — revisit with real numbers then, not
speculatively now.

---

## Phase 5 — Implementation Roadmap (prioritized by business value)

1. **Evidence model (Phase 2.2) + wire into existing enforcer/decision-engine
   output.** Highest leverage: makes every existing finding immediately more
   trustworthy with no new pipeline, directly serves the "Ortho makes
   engineering decisions safer" positioning, and is scoped to ~1-2 packages.
2. **Unify `guardrails()`+`decide()`+impact into `review()` (Phase 1.3, 3.1).**
   Second-highest leverage: this is the entire "one command, one report" product
   experience the source document wants, and it's mostly wiring existing,
   working pieces together — low implementation risk, high experience payoff.
3. **Accept/reject feedback loop (Phase 2.4).** Unlocks the specific "this was
   rejected before, here's why" memory example from the source document. Small
   surface, but requires a new user habit (running `ortho feedback`) to pay off
   — budget for the fact that adoption of this specific action, not just the
   passive citation feature already shipped, is unproven.
4. **Structured citation queries (Phase 2.3, 3.4).** Precision improvement on
   an already-shipped feature — do after 1-3, not before, since it's a quality
   multiplier on existing functionality rather than new capability.
5. **Repository Q&A (Phase 3.7).** Explicitly last. Zero existing code, real
   R&D risk, competes directly with the most crowded part of the market
   (chat-with-code tools), and — per the earlier competitive analysis — is the
   least differentiated capability in the whole vision. Only pursue after 1-4
   are shipped and the false-positive rate / review-adoption metrics from a
   real pilot justify the investment.

Do not build streaming/caching (4.4) or the full ADR/Slack/incident ingestion
surface described in the original Pillar 3 in this window — both are
explicitly out of scope per the earlier critical review (unbounded integration
surface, no proven pull from a single pilot yet).

---

## Phase 6 — Competitive Analysis (delta-specific, not repeated from the earlier review)

**Why competitors can't easily copy the Evidence model specifically:** a
`list[str]` evidence field is copyable in an afternoon. A type-level invariant
that *forbids constructing a finding without evidence* is a design discipline,
not a feature — it has to be baked into the whole review pipeline from the
start, or retrofitted at real cost later. Ortho retrofitting it now, while the
codebase is still small, is cheaper than a funded competitor retrofitting it
into an established product surface with existing customer-facing report
formats to not break.

**Where Ortho is still weak, concretely, after this delta:** even with
Evidence built, the underlying architecture-style classifier has a documented,
verified 75%-vs-83.3% accuracy gap on its own benchmark. Evidence makes a wrong
finding *more legible*, not *less wrong*. This is not solved by anything in
this document and should not be marketed as solved.

**What remains the long-term moat:** unchanged from the earlier review —
local-first memory that compounds per-repo, structurally inaccessible to
cloud-tied competitors (Bito, cubic, Gemini Code Assist). Nothing in this delta
changes that assessment; the Evidence model strengthens the review pillar but
doesn't touch the moat pillar.

**What should never be built:** confirmed from the earlier review —
user-facing confidence percentages as headline UX, full ADR/Slack/incident
ingestion before a pilot demands it, and general NL repository chat as
anything other than last-priority, narrowly-scoped graph-query translation
(3.7) — not open-ended RAG.
