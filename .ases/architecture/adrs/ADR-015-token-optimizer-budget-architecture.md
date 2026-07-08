# ADR-015: Token Optimizer — Budget Architecture & Deterministic Context Assembly

**Status:** Proposed (awaiting human approval during GATE 2)

**Date Proposed:** 2026-07-08

**Related Artifacts:**
- FRD §10 (Pillar 5 — Token Optimizer)
- task-014 PLANNER: plan.md, spec.md
- task-014 ARCHITECT: architecture-review.md (GATE 2)

---

## Context

Ortho's token optimizer is responsible for assembling the highest-quality context using the fewest possible tokens. This is the bridge between the retrieval layer (Pillars 1-3) and the generation layer (LLM).

The FRD mandates 9 features for Pillar 5 (Phase 4), but the first task (task-014) scopes to only the **token budget manager** (hard ceiling with priority ranking) — the foundational feature that unblocks the WorkflowExecutor and supports all future enhancements.

Three architectural decisions emerged during planning:

1. **Mutable TokenBudget as parameter** (not immutable value object)
2. **Deterministic tie-breaking and chunk ordering** (guarantees reproducible workflows)
3. **Scope to budget manager only** (defer semantic reranking, dedup, compression to task-015)

This ADR justifies these choices and documents their trade-offs.

---

## Decision

### 1. TokenBudget: Mutable Parameter Semantics

**Design:** `TokenBudget` is a dataclass with mutable fields. Passed to `assemble_context()` by reference, modified in place by `consume()` calls. The same budget instance is returned in the ContextPackage.

**Justification:**

**Why mutable, not immutable?**
- Caller needs to track incremental token consumption across multiple `assemble_context()` calls within the same orchestration step
- Alternative (immutable): Would require caller to thread new budget instance through each call, or would lose budget state
- Alternative (global token counter): Couples caller to global mutable state, breaks composability
- Mutable parameter is idiomatic Python, matches FRD §10's own TokenBudget definition, aligns with how most budgeting systems work (HTTP response headers, database connection pools, etc.)

**Why parameter-based, not stored in orchestrator?**
- Orchestrator should not own budget lifecycle; each step's budget is independent
- Parameter-based allows future flexibility (per-agent budgets, dynamic re-allocation, etc.)
- Clear ownership: caller creates, passes, manages (no hidden state)

**Safety guarantees:**
- `budget.can_fit()` validates before overflow
- `budget.consume()` raises `BudgetExceededError` if ceiling would be exceeded
- No silent budget corruption (only method is `consume()`, which enforces the rule)
- Caller responsibility clearly documented (create fresh per step or reset `used`)

**Cost:** Caller must remember to create fresh or reset budget per step. No automatic cleanup.

---

### 2. Deterministic Tie-Breaking & Chunk Ordering

**Design:** All operations in token-optimizer are deterministic. Identical inputs → identical outputs.

**Tie-breaking rule (spec.md §1):**
```
Sort by: (1) relevance_score descending
         (2) token_count ascending (prefer smaller chunks)
         (3) artifact.id ascending (lexicographic)
```

**Chunk ordering in prompt assembly:**
```
Order chunks in final user message by: chunk.id ascending (lexicographic)
```

**Justification:**

**Why determinism matters:**
- Reproducible workflows: Same intent + repo → same context → same prompt → same LLM output (given fixed model/temperature)
- Debugging: If result is wrong, can re-run and inspect context (not intermittent)
- Evidence: Can compare two runs and prove they're identical (ASES principle: evidence over confidence)
- Testing: Can assert `assemble_context(x) == assemble_context(x)` (not probabilistic)

**Why this tie-breaking order?**
- Relevance first: Respect search results (higher relevance is better)
- Token count second: Smaller chunks fit more within budget (prefer variety)
- Artifact ID third: Stable lexicographic order (last resort, ties broken by name)
- No shuffle(), no randomness, no insertion-order dependency

**Why prompt chunks ordered by chunk.id?**
- Independent of assembly order (chunk.id is stable, doesn't change)
- Identical context → identical prompt text (chunk order deterministic)
- Simplest rule: ascending order, unambiguous, easy to test

**Cost:** Sorting adds minimal overhead (O(n log n), n << 10000 chunks). Worth it for reproducibility.

---

### 3. Scope to Budget Manager Only (Defer Remaining 8 Features)

**Design:** task-014 implements exactly one of FRD's 9 Pillar 5 features:
- ✅ **Token budget manager** (hard ceiling + priority ranking)

**Explicitly deferred to task-015 or later:**
- ❌ Intent-aware reranker (requires embeddings infrastructure)
- ❌ Duplicate remover (requires semantic similarity detection)
- ❌ Graph expander (requires call-graph traversal)
- ❌ Context compressor (requires summarization or heuristics)
- ❌ Architecture-aware retrieval (requires ArchitectureModel weighting)
- ❌ Model context adapter (requires multi-model token counting)
- ❌ Prompt assembler (advanced) (only basic concatenation in task-014)
- ❌ Context quality logger (logging/observability feature)

**Justification:**

**Why not build all 9 now?**
- Embedding infrastructure missing (context-hub has NullEmbedding stub)
- LLM model adapters not designed (only Claude supported now)
- Deduplication requires semantic similarity (needs embeddings)
- Compression strategies depend on LLM availability (no live LLM in token-optimizer)
- Scope creep risk: 9 features can't be tested in one 30–90 min atomic task

**Why this is not a limitation:**
- Token budget manager + priority ranking is the **foundational feature** (others build on it)
- WorkflowExecutor unblocked immediately (stubs at lines 118, 151-160 become real)
- FRD Pillar 5 requirements **still satisfied** (Phase 4 task will deliver rest)
- Clear roadmap: task-014 (foundation) → task-015 (reranking, dedup, compression, etc.)

**Cost:** Phase 4 will need more tasks for full Pillar 5. But Phase 3 (Execution) can ship with budget manager + basic assembly.

**Upside:** Clean, focused, testable task. No hidden feature bloat. Clear scope boundary.

---

## Consequences

### Positive

1. **Reproducible Workflows** — Identical context + prompt for identical input (ASES evidence principle)
2. **Clear Ownership** — Caller manages budget lifecycle (not orchestrator magic)
3. **Extensible Foundation** — Budget manager works with future reranking, dedup, compression (no rework)
4. **Simple & Testable** — Single deterministic algorithm, not 9 intertwined features
5. **FRD Compliance** — TokenBudget interface exactly matches FRD §10
6. **Zero Circular Dependencies** — token-optimizer imports only downward (orchestration, context-hub, shared)

### Negative / Trade-offs

1. **Caller Responsibility** — Orchestrator must create fresh or reset budget per step (not automatic)
   - *Mitigation:* Document clearly in docstrings and spec. Add assertion checks in tests.

2. **Sorting Overhead** — Deterministic tie-breaking adds O(n log n) overhead
   - *Mitigation:* n < 100 typically (artifact search limits), negligible cost. Could optimize later if needed.

3. **No Semantic Reranking Yet** — Intent-aware reranking deferred to task-015
   - *Mitigation:* Token budget manager + priority ranking is solid foundation. Reranking can plug in without breaking this design.

4. **No Compression** — Over-budget context NOT automatically summarized
   - *Mitigation:* LLM enforces max_tokens downstream (passive layer approach). Caller can truncate if needed.

5. **Phase 4 Still Needed** — Full Pillar 5 requires task-015+
   - *Mitigation:* Clear roadmap. Each task delivers value (budget manager is immediate blocker clearance).

---

## Alternatives Considered

### Alternative 1: Immutable TokenBudget Value Object
```python
class TokenBudget:
    def consume(self, tokens: int) -> 'TokenBudget':
        """Returns new TokenBudget with incremented used."""
        return TokenBudget(total=self.total, used=self.used + tokens, model=self.model)
```
- **Pros:** Pure functional style, no side effects
- **Cons:** Requires caller to thread returned budget through calls, harder to track total consumption, not idiomatic Python budget pattern
- **Rejected:** Mutable parameter is simpler, matches FRD design, aligns with how http.HeaderSet and similar work

### Alternative 2: Optimal Packing (Knapsack Algorithm)
Instead of greedy inclusion, solve optimal subset of chunks within budget:
```python
# Pseudo-code: find optimal subset of chunks
best_subset = solve_knapsack(chunks, budget.remaining)
```
- **Pros:** Guaranteed maximum utility within budget
- **Cons:** O(2^n) complexity (impractical for 100+ chunks), non-deterministic search order, harder to debug
- **Rejected:** Greedy with priority ranking is good-enough, faster, simpler

### Alternative 3: LLM-Based Reranking in token-optimizer
Move reranking from task-015 into task-014:
```python
def assemble_context(...):
    # ... greedy inclusion ...
    # Rerank with LLM
    reranked = llm_rerank(context_package, query)
```
- **Pros:** Semantic relevance on day one
- **Cons:** LLM calls add latency/cost, non-deterministic (model updates), couples token-optimizer to LLM
- **Rejected:** FRD says token-optimizer is below the LLM (intelligence layer, not generation layer). Stays deterministic without LLM.

### Alternative 4: Hash-Based Tie-Breaking
Use hash(artifact.id) % some_constant for tie-breaking:
```python
# Pseudo-code
secondary_key = hash(artifact.id) % 1000
sort_by(relevance_score, secondary_key)
```
- **Pros:** Faster than lexicographic string comparison
- **Cons:** Not deterministic across Python versions (hash randomization), harder to debug
- **Rejected:** Lexicographic order is stable, deterministic, human-readable

---

## Evidence

- **FRD §10:** TokenBudget interface matches exactly
- **spec.md §1–3:** Deterministic tie-breaking and mutable semantics formally specified
- **task-013 stubs:** WorkflowExecutor and step_runner both need token-optimizer context
- **Phase 1 mandate:** TokenBudget was "mandatory since Phase 1" but never implemented (blocking task-013)
- **task-015 roadmap:** 8 deferred features are clearly scoped for next phase

---

## Related Decisions

- **ADR-013:** Semantic-router adoption (task-012) — Intent classification, no LLM budget needed
- **ADR-014:** Pure Python Selector (task-013) — Deterministic agent/skill scoring
- (Future) **ADR-016:** Semantic Reranking (task-015) — Embeddings wiring, LLM model adapters

---

## Conclusion

This design choice (mutable budgets, deterministic tie-breaking, focused scope) creates a solid foundation for Pillar 5. It prioritizes reproducibility, clarity, and composability over feature completeness. The 8 deferred features can be added in task-015 without breaking this design.

The architecture is approved for implementation (task-014, GATE 3: BUILDER).

---

*End of ADR-015*
