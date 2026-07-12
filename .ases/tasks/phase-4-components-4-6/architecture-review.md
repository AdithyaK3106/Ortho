# Architecture Review: Phase 4 Components 4–6

**Task ID:** phase-4-components-4-6  
**Reviewer Role:** ARCHITECT (ASES workflow)  
**Date:** 2026-07-12  
**Verdict:** ✅ APPROVED  

---

## Module Boundaries & Coherence

### Component 4: Context Compressor (`compressor.py`)

**Scope:** Summarization logic only.

**Public API:**
```python
compress_over_budget(
    context_package: ContextPackage,
    compression_target: float,
    summarization_model: str,
) -> ContextPackage
```

**Dependencies:**
- `token_optimizer.types` (ContextChunk, ContextPackage) ✓ same package
- `anthropic` API (external) ✓ already in orchestration
- `tiktoken` (external) ✓ token counting (trusted library)
- No circular dependencies ✓

**Cohesion:** High. Pure function, no side effects (except API call).

### Component 5: Architecture-Aware Retrieval (`arch_retrieval.py`)

**Scope:** Retrieval weight boosting based on arch model.

**Public API:**
```python
boost_by_architecture(
    chunks: list[ContextChunk],
    architecture_model: ArchitectureModel | None,
    centrality_weights: dict | None,
) -> list[ContextChunk]
```

**Dependencies:**
- `token_optimizer.types` (ContextChunk) ✓ same package
- `arch_intelligence.types` (ArchitectureModel) ✓ imported (one-way)
- No circular dependencies ✓

**Cohesion:** High. Pure function, deterministic reranking.

### Component 6: Model Context Adapter (`model_adapter.py`)

**Scope:** Prompt format adjustment per model.

**Public API:**
```python
adapt_prompt_for_model(
    system_prompt: str,
    user_message: str,
    model: str,
) -> tuple[str, str]
```

**Dependencies:**
- Standard library only (str, tuple) ✓
- No external imports ✓
- No circular dependencies ✓

**Cohesion:** Very high. Pure text transformation.

---

## Layer Dependencies (ADR-015 Compliance)

Current token-optimizer layer structure (one-way):

```
orchestration → token-optimizer → shared/types
```

**New additions:**
- Component 4: Adds `anthropic` dependency (OK: orchestration uses it)
- Component 4: Adds `tiktoken` dependency (OK: token counting utility)
- Component 5: Adds `arch-intelligence` import (OK: read-only, no reverse)
- Component 6: No new dependencies ✓

**Verdict:** ✅ Complies with ADR-015 (layered imports, acyclic)

---

## API Contracts (Input/Output)

### Component 4: Context Compressor

**Input Contract:**
- ContextPackage: valid object with chunks list (may be empty)
- compression_target: float in [0.0, 1.0]
- summarization_model: str (known model ID)

**Output Contract:**
- ContextPackage: new instance (input unchanged)
- chunk.content: summarized (shorter) or original (on error)
- chunk.token_count: recomputed via tiktoken
- chunk.relevance_score: unchanged
- chunk.included: unchanged

**Error Handling:**
- Invalid compression_target: raise ValueError
- Unknown model: raise ValueError
- API timeout (3 retries): fallback to return uncompressed
- API rate limit: retry with exponential backoff

### Component 5: Architecture-Aware Retrieval

**Input Contract:**
- chunks: list of ContextChunk (may be empty)
- architecture_model: ArchitectureModel or None
- centrality_weights: dict or None (uses default)

**Output Contract:**
- Same chunks, relevance_score modified
- Resorted by score descending, then chunk.id
- No new chunks added or removed

**Error Handling:**
- Null architecture_model: identity (return unchanged)
- Symbol not found in architecture: 1.0x (no boost)
- Invalid centrality_weights: use defaults

### Component 6: Model Context Adapter

**Input Contract:**
- system_prompt: str (any length, any content)
- user_message: str (any length, any content)
- model: str (model identifier)

**Output Contract:**
- Tuple of (adapted_system, adapted_user)
- Both are str, non-empty if inputs non-empty

**Error Handling:**
- Unknown model: identity (return input unchanged)
- Empty prompts: return empty (identity)

---

## Data Flow & Validation

**Integration Point (Phase 4 Pipeline):**

```
assemble_context()
  ↓
detect_and_remove_duplicates() [component 1]
  ↓
rerank_by_intent() [component 2]
  ↓
expand_by_call_graph() [component 3]
  ↓
boost_by_architecture() [component 5] ← NEW
  ↓
compress_over_budget() [component 4] ← NEW (if budget exceeded)
  ↓
adapt_prompt_for_model() [component 6] ← NEW
  ↓
prompt_assembler()
  ↓
LLM
```

**Validation Points:**
- Component 4: Validates compression_target ∈ [0.0, 1.0] ✓
- Component 5: Validates chunks list (accepts empty) ✓
- Component 6: No validation needed (all str inputs valid) ✓

---

## Risks & Mitigations

### Risk 1: LLM API Timeouts (Component 4)

**Impact:** High. Summarization required for budget compliance.

**Likelihood:** Medium (network issues possible).

**Mitigation:**
- Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
- Fallback: Return uncompressed (loose budget but preserve output)
- Cache by chunk.id (reduce API calls on repeated queries)
- Timeout: 10 seconds per request

**Owner:** Test Designer (verify retry behavior)

### Risk 2: Architecture Model Missing (Component 5)

**Impact:** Medium. Retrieval less optimized, but not broken.

**Likelihood:** High (arch detection may fail or be skipped).

**Mitigation:**
- Check `if architecture_model is None:` early, return identity
- Graceful degradation: no boost is correct behavior
- Fallback heuristic: if symbol not found, try file-level matching

**Owner:** BUILDER (implement check)

### Risk 3: Model Format Assumptions Wrong (Component 6)

**Impact:** Medium. Prompt quality may degrade for specific models.

**Likelihood:** Low (models well-documented).

**Mitigation:**
- Conservative changes (only remove verbose for Haiku)
- Fallback to identity for unknown models
- All rules commented with model-specific reasoning
- Integration test with sample prompts

**Owner:** Test Designer (verify per-model behavior)

---

## Scalability & Performance

### Component 4: Context Compressor

- Per-chunk API call: ~200ms (averaged)
- Max chunks to compress: 20 (max_additions from earlier)
- Total latency: ~4 seconds worst case
- Caching: Reduces repeated summaries to O(1)

**Acceptable:** Yes (4s latency is reasonable for context assembly)

### Component 5: Architecture-Aware Retrieval

- Per-chunk lookup: O(1) hash lookup in ArchitectureModel
- Resorting: O(n log n) where n=chunks
- Max chunks: 50 (typical context package)
- Total latency: ~5ms

**Acceptable:** Yes (negligible)

### Component 6: Model Context Adapter

- String processing: O(n) where n=prompt length
- Typical prompt: 2KB–5KB
- Total latency: <1ms

**Acceptable:** Yes (negligible)

---

## Extensibility & Future Changes

### Component 4: Context Compressor

- ✅ Extensible: New summarization models easily added
- ✅ Config-driven: compression_target configurable
- ⚠️ Limitation: Only Anthropic API (could add other providers later)

### Component 5: Architecture-Aware Retrieval

- ✅ Extensible: New arch styles supported via centrality_weights
- ✅ Config-driven: weights customizable per deployment
- ✅ Graceful: Unknown styles default to no boost

### Component 6: Model Context Adapter

- ✅ Extensible: New model families added as rules
- ✅ Config-driven: Rules could move to config file (future)
- ✅ Fallback: Unknown models default to identity

---

## Security Considerations

### Component 4

- **Input validation:** compression_target range check ✓
- **API key exposure:** Use environment variable (ANTHROPIC_API_KEY) ✓
- **Output:** Summarization may strip sensitive data (desired) ✓

### Component 5

- **Input validation:** Null check on architecture_model ✓
- **Privilege escalation:** No (read-only access to arch model) ✓

### Component 6

- **Input validation:** No validation needed (string inputs always valid) ✓
- **Output encoding:** No changes needed (ASCII safe) ✓

**Verdict:** ✅ No security issues identified

---

## ADR Requirements

**No new ADRs required.** All decisions align with existing:
- ADR-004: Storage (SQLite) — not changed ✓
- ADR-014: Selector Engine (pure Python) — not changed ✓
- ADR-015: Layer boundaries — maintained ✓

All three components respect existing architectural constraints.

---

## Verdict

✅ **APPROVED — Proceed to BUILDER**

**Summary:**
- Module boundaries coherent and non-overlapping
- API contracts clear and testable
- Dependencies acyclic, one-way imports enforced
- Error handling defined with fallbacks
- Scalability and performance acceptable
- Security review clean
- No new ADRs needed

**Conditions for proceeding:**
- Implement per spec.md
- Test coverage ≥50 cases across components
- All tests pass before submission to GATE 4
- Implementation notes document any deviations

**Next Phase:** BUILDER (implement components 4–6)

---

## Sign-off

**Architecture Reviewer:** ASES Workflow  
**Approval Date:** 2026-07-12  
**Status:** Ready for BUILDER  
