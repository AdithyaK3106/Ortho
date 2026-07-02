# ADR-010: Reuse Discovery Algorithm — AST-Type-Sequence Edit Distance, Not Embeddings

**Status:** PROPOSED
**Date:** 2026-07-02
**Author:** ARCHITECT
**Approved by:** [Pending human approval]

---

## Context

Task-010 implements reuse discovery (FRD Pillar 3 feature, line 853): find structurally similar
code patterns across files, so duplicated logic can be surfaced for potential consolidation.

Ortho's storage layer (ADR-004) is local-first SQLite, with `sqlite-vec` reserved for Pillar 2
(ContextHub)'s semantic search over natural-language artifacts (docs, commit messages). Pillar 3
(Architectural Intelligence) has so far used deterministic, evidence-backed algorithms exclusively
(task-008's Louvain clustering + topological sort, task-009's BFS blast-radius + weighted scoring)
— no embeddings, no ML models, anywhere in this pillar.

`ReuseDetector` needs a similarity measure between two function/method bodies that is: (a)
deterministic, (b) explainable via an evidence trail (matching Pillar 3's established pattern),
and (c) doesn't require a new class of infrastructure (an embedding model, a vector index) for a
task whose scope is explicitly bounded to "find similar code patterns," not "semantic code search."

---

## Problem Statement

**How should Ortho measure structural similarity between two code symbols?**

Options:
1. **Text diff** — line-based or character-based diff (e.g. `difflib` on raw source text)
2. **Embeddings + vector similarity** — encode each symbol via a code embedding model, compare
   via cosine similarity in `sqlite-vec`
3. **AST-type-sequence edit distance** — parse each symbol to its AST, flatten to a sequence of
   node *type* labels (dropping identifier names and literals), compare via edit distance

---

## Alternatives Considered

### Option A: Text Diff (Raw Source Comparison)

**Description:** Compare symbol bodies as raw text using `difflib.SequenceMatcher` or line-based
diff directly on source code.

**Pros:**
- Simplest possible implementation, zero new logic beyond stdlib `difflib`
- No AST re-parsing needed

**Cons:**
- ❌ Fails the core goal: two functions with identical logic but different variable/parameter
  names (the most common real-world duplication pattern — e.g. `validate_user` vs
  `validate_account` with identical branching) score as dissimilar under text diff, since every
  identifier differs
- ❌ Sensitive to formatting (whitespace, line breaks, comment placement) that has no bearing on
  structural similarity
- ❌ Would not satisfy the acceptance criterion "identifies structurally similar symbols whenever
  qualifying duplicates exist" — text diff finds textual duplicates, a narrower and less useful set

**Verdict:** ❌ **Rejected** — doesn't solve the actual problem (structural reuse, not textual
copy-paste detection).

---

### Option B: Embeddings + Vector Similarity

**Description:** Encode each symbol's source into a vector via a code embedding model (e.g. a
small local code-embedding model, or an API-based one), compare via cosine similarity, optionally
indexed in the existing `sqlite-vec` extension (already present for Pillar 2).

**Pros:**
- Would also catch *semantic* similarity (different structure, same intent) — a broader net than
  structural comparison
- Reuses existing `sqlite-vec` infrastructure already accepted for Pillar 2

**Cons:**
- ❌ Breaks local-first-no-ML-dependency precedent for Pillar 3 specifically — every other Pillar
  3 detector (task-008, task-009) is a pure deterministic algorithm over graphs/AST, explainable
  without a model. This task's plan.md explicitly scoped out "embeddings-based semantic reuse
  detection" for this reason (Scope Out, item 1)
  - If a local embedding model is used: adds a non-trivial new dependency (model weights, runtime)
    for a task otherwise addable in stdlib
  - If an API-based embedding model is used: breaks local-first entirely (network dependency,
    the opposite of ADR-004's SQLite-local-first decision)
- ❌ Not deterministic in the same strict sense — embedding models can have version-dependent
  outputs, floating-point non-determinism across hardware, and results that are much harder to
  explain via a human-readable evidence string (a vector distance number isn't "evidence" in the
  same sense as "both functions: 1 if-branch, 2 calls, 1 return")
- ❌ Conflates two different Pillar boundaries: semantic similarity of natural-language-adjacent
  content is Pillar 2 (ContextHub)'s territory per the FRD; Pillar 3's job is structural/graph
  analysis of code, not semantic retrieval

**Verdict:** ❌ **Rejected** — correctly excluded in plan.md's Scope (Out) section; this ADR
formalizes and justifies that exclusion rather than revisiting it.

---

### Option C: AST-Type-Sequence Edit Distance (Chosen)

**Description:** Parse each symbol's source range to a tree-sitter subtree (reusing the parser
already set up by `SymbolExtractor` — no new parsing infrastructure), flatten the subtree to a
sequence of AST node *type* labels only (dropping identifier names, literal values, and comments),
then compute similarity as `1 - (levenshtein(seq_a, seq_b) / max(len(seq_a), len(seq_b)))`.
Bucket candidates by `(Symbol.type, line_count // 5)` before pairwise comparison to keep the
overall complexity near-linear in practice.

**Pros:**
- ✅ Structural, not textual: two functions with identical control-flow shape but different
  identifiers score highly similar (the actual goal), while two functions with different logic
  but coincidentally similar text do not
- ✅ Deterministic: same AST, same node-type sequence, same edit distance, every time — no
  model, no floating-point non-determinism across hardware
- ✅ Explainable: evidence strings can cite concrete structural facts ("both functions: 1
  if-branch, 2 calls, 1 return") derived directly from the same node-type sequence used for
  scoring — not an opaque distance number
- ✅ Zero new dependencies: reuses `SymbolExtractor`'s existing tree-sitter parser setup (already
  a dependency, already accepted); edit distance computed via stdlib `difflib.SequenceMatcher`
  by default (see rollback-plan.md Scenario 4 — a dedicated Levenshtein library is only added if
  a documented performance failure requires it)
- ✅ Consistent with Pillar 3's established pattern: task-008 (Louvain clustering, topological
  sort) and task-009 (BFS, weighted scoring) are both pure deterministic algorithms over
  graph/AST structure — this continues that pattern rather than introducing a new one
- ✅ Bucketing by type+size keeps the O(n²) pairwise comparison tractable without needing an
  approximate-nearest-neighbor index (which embeddings would otherwise require)

**Cons:**
- ❌ Cannot distinguish two functions with identical shape but opposite logic (e.g. `if x > 0`
  vs `if x < 0` — both produce the same node-type sequence since the AST node type for a
  comparison is the same regardless of operator). Documented as Known Limitation 3 in spec.md;
  upgrade path (comparing a richer node label combining type + operator) is noted but deferred
  until proven necessary
- ❌ Purely syntactic — will not catch semantically equivalent code written with different
  control-flow shape (e.g. a `for` loop vs a list comprehension doing the same thing). This is an
  accepted trade-off, not a defect: catching that class of similarity is exactly the embeddings
  approach this ADR rejects for Pillar 3

**Verdict:** ✅ **Selected** — the only option that is simultaneously structural (solves the
actual duplication-detection goal), deterministic, explainable, dependency-free, and consistent
with Pillar 3's existing architectural pattern.

---

## Decision

**`ReuseDetector` measures symbol similarity via AST-node-type-sequence edit distance, computed
over `SymbolExtractor`'s existing tree-sitter parse output — not text diff, not embeddings.**

### Core Components

1. **Module:** `packages/arch-intelligence/src/arch_intelligence/reuse_detector.py`
   - `ReuseDetector.find_similar(symbols_by_file, sources_by_file, threshold=0.7) -> list[ReuseCluster]`

2. **Algorithm** (already specified, referenced not restated here): see
   `.ases/tasks/task-010-adr-awareness-reporting/spec.md`, "Similarity Algorithm (ADR-010)"

3. **Data type:** `ReuseCluster` dataclass — `symbol_ids`, `file_ids`, `similarity`, `evidence`

4. **Threshold policy:** `0.7` is a Phase 2 default, caller-configurable (CLI `--threshold` or
   direct API call) — see spec.md "Threshold Configuration Policy." This ADR fixes the
   *algorithm*, not the *threshold*; recalibrating the default later requires no architectural
   change.

---

## Rationale

1. **Solves the stated problem, not an adjacent one:** "Find structurally similar code patterns"
   (FRD line 853) is a structural comparison problem. AST-type-sequence edit distance measures
   exactly that; embeddings measure semantic similarity, a related but different (and, per FRD,
   Pillar-2-owned) problem.

2. **Local-first consistency:** No network call, no model weights, no GPU/inference requirement.
   Matches ADR-004 (storage strategy) and ADR-009 (this task's other decision) in keeping Ortho's
   Phase 1–2 footprint dependency-light and fully offline-capable.

3. **Determinism as a hard requirement:** Pillar 3's confidence-score model (FRD line 856-868)
   requires every detection result to carry an evidence list — this only works cleanly with an
   algorithm whose output can be traced back to concrete structural facts, which edit distance
   over explicit node-type sequences provides and embedding-space distance does not.

4. **No premature infrastructure:** `sqlite-vec` exists in this codebase (task-004, Pillar 2) but
   adding it to Pillar 3 for this task would be infrastructure reuse for its own sake, not because
   the problem requires it — the AST-based approach solves the stated goal without it.

---

## Consequences

### Positive

- No new dependency added to `packages/arch-intelligence/pyproject.toml` by default
- `ReuseDetector` output is auditable: every cluster's evidence traces to concrete AST structure
- Consistent mental model across all of Pillar 3: every detector (arch style, layers, subsystems,
  impact, debt, dependency health, reuse) is a deterministic algorithm over graphs/AST, none are
  ML-based

### Negative

- Will not catch semantically-equivalent-but-structurally-different duplication (e.g. loop vs
  comprehension) — accepted, this is Pillar 2's problem space if ever pursued
- Will conflate structurally-identical-but-logically-opposite code (Known Limitation 3) — accepted
  with a documented, deferred upgrade path

### Neutral

- Performance is bounded by the bucketing strategy (spec.md's Benchmark Environment section
  documents how this is measured and why timing assertions use a generous ceiling, not an exact
  value)

---

## Future Considerations

### If Semantic (Not Just Structural) Reuse Detection Is Wanted Later

**Scenario:** A future phase wants to catch semantically-equivalent-but-structurally-different
duplication (the class of similarity this ADR explicitly excludes).

**Mitigation:** This would be a new, separate capability — likely built on Pillar 2's existing
`sqlite-vec` infrastructure and embedding pipeline (task-004), not a modification to
`ReuseDetector`. It would warrant its own ADR and its own FRD line item, since it crosses the
Pillar 2/Pillar 3 boundary this ADR deliberately preserves.

**Current decision:** Not needed for task-010; `ReuseDetector`'s structural algorithm stands on
its own as the Pillar 3 reuse-discovery feature.

### If False Positives from Operator-Blind Comparison Prove Common

**Scenario:** Real-world use of `ReuseDetector` surfaces many clusters that are structurally
identical but logically opposite (Known Limitation 3), reducing signal quality.

**Mitigation:** Upgrade the node-type label to include the operator for comparison/binary-op
nodes specifically (a small, additive change to the flattening step — not a re-architecture of
the edit-distance approach itself).

**Current decision:** Not implemented preemptively; revisit only if real usage shows this is a
practical problem, per plan.md's risk mitigation philosophy.

---

## Related Tasks

- **task-010:** ADR Awareness + Reporting (this task, Week 13–14)
- **task-008:** Architecture Detection (established Pillar 3's deterministic-algorithm pattern
  this ADR continues)
- **task-009:** Impact Analysis + Debt Scoring (same pattern, applied to graph traversal instead
  of AST comparison)
- **task-004:** ContextHub (owns `sqlite-vec` and embeddings — explicitly not reused here, and
  the boundary this ADR preserves)

---

## Related ADRs

- **ADR-009:** ADR Cross-Reference Strategy — same task, same local-first/stdlib-first/
  deterministic reasoning applied to markdown text extraction instead of code structure
- **ADR-004:** Storage Strategy (SQLite local-first) — the precedent this decision extends into
  Pillar 3's algorithm choices
- **ADR-005:** Language Adapter Plugin Model — `ReuseDetector` reuses `SymbolExtractor`'s
  tree-sitter parser setup rather than introducing a second parsing path, consistent with this
  ADR's "one adapter owns language-specific parsing" principle

---

*End of ADR-010*
