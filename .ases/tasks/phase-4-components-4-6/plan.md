# Phase 4 Components 4–6 Build Plan

**Task ID:** phase-4-components-4-6  
**Feature:** Context Compressor, Architecture-Aware Retrieval, Model Context Adapter  
**Phases:** 4–5 days  
**ASES Status:** DRAFT → PLANNED → ARCH-REVIEW → READY-TO-BUILD  

---

## Feature Summary

Build three critical token optimization components for Phase 4:
1. **Context Compressor** — Summarize low-priority chunks when over budget (LLM-based)
2. **Architecture-Aware Retrieval** — Boost architecturally central modules by 1.2–1.5x
3. **Model Context Adapter** — Adjust prompt format per LLM (Opus vs Haiku vs GPT)

These three enable Phase 4 exit criteria: ≥15% token reduction from Phase 3 baseline.

---

## Atomic Task Breakdown

### Task A: Context Compressor (2 days)

**Objective:** Implement LLM-based summarization of over-budget chunks.

**Acceptance Criteria:**
- [ ] `compress_over_budget()` accepts ContextPackage, compression_target (0.0–1.0)
- [ ] Only `included=False` chunks summarized (already marked low-priority)
- [ ] Uses Anthropic API (claude-haiku for cost)
- [ ] Token count recomputed via tiktoken
- [ ] Deterministic: same input → same summary (caching by chunk.id)
- [ ] All 15+ test cases pass (boundary, budget, quality, error cases)
- [ ] No external calls in tests (mocked API)

**Input:**
- ContextPackage (from token-optimizer.types)
- compression_target: float
- API key via environment

**Output:**
- New ContextPackage with compressed content
- Chunk.token_count updated
- High-priority chunks (included=True) untouched

**Files to create:**
- `packages/token-optimizer/src/token_optimizer/compressor.py`
- `packages/token-optimizer/tests/test_compressor.py`

**Files to modify:**
- `packages/token-optimizer/src/token_optimizer/__init__.py` (add exports)

**Files NOT to touch:**
- Any repo-intelligence, context-hub, orchestration packages
- Any CLI commands

**Risks:**
- LLM API timeouts → retry logic required
- Summarization quality varies → spot-check needed
- Token count estimation inaccuracy → use tiktoken (proven)

**Mitigations:**
- Retry 3x with exponential backoff
- Cache summaries by chunk.id
- Fallback to identity (no compression) on API error

---

### Task B: Architecture-Aware Retrieval (1.5 days)

**Objective:** Weight chunks by architectural centrality.

**Acceptance Criteria:**
- [ ] `boost_by_architecture()` accepts chunks list + ArchitectureModel
- [ ] Supports all arch styles (layered, microservices, flat, hexagonal)
- [ ] Layer-based boost: central layers 1.5x, peripheral 1.0x
- [ ] Subsystem boost: low-coupling 1.2x, high-coupling 1.0x
- [ ] Non-matching chunks get 1.0x (no change)
- [ ] All 12+ test cases pass (styles, layers, subsystems, edge cases)
- [ ] No external dependencies beyond existing (uses ArchitectureModel from arch-intelligence)

**Input:**
- Chunks list
- ArchitectureModel (from arch-intelligence)
- centrality_weights: config dict (default provided)

**Output:**
- Same chunks, relevance_score boosted, resorted

**Files to create:**
- `packages/token-optimizer/src/token_optimizer/arch_retrieval.py`
- `packages/token-optimizer/tests/test_arch_retrieval.py`

**Files to modify:**
- `packages/token-optimizer/src/token_optimizer/__init__.py`

**Risks:**
- ArchitectureModel may be None (not yet detected) → fallback to identity
- Symbol-to-architecture mapping incomplete → heuristic matching

**Mitigations:**
- Check if arch_model exists; skip boost if None
- Use file-level matching if symbol not found

---

### Task C: Model Context Adapter (1 day)

**Objective:** Adjust prompt assembly per LLM model.

**Acceptance Criteria:**
- [ ] `adapt_prompt_for_model()` accepts system_prompt, user_message, model string
- [ ] Supports: claude-opus-4-8, claude-haiku-4-5, gpt-4, gpt-4o, local models
- [ ] Opus: identity (no changes)
- [ ] Haiku: remove verbose sections, prioritize essentials
- [ ] GPT-4: adjust format (different token counting)
- [ ] Local: add budget warnings
- [ ] All 10+ test cases pass (per-model, fallback, edge cases)
- [ ] No external calls (pure text transformation)

**Input:**
- system_prompt: str
- user_message: str
- model: str (identifier)

**Output:**
- (adapted_system, adapted_user)

**Files to create:**
- `packages/token-optimizer/src/token_optimizer/model_adapter.py`
- `packages/token-optimizer/tests/test_model_adapter.py`

**Risks:**
- Unknown model IDs → fallback to identity
- GPT-4 format assumptions wrong → test with real examples

**Mitigations:**
- Fallback rule: unknown model → identity (no change)
- Comment all model-specific rules with reasoning

---

## Task Dependencies

```
A (Compressor) → independent
B (Arch Retrieval) → depends on arch-intelligence import
C (Model Adapter) → independent

All three can be built in parallel (no cross-dependencies)
```

---

## Test Strategy

**Parallel Test Designer** (via fork):
- Write 50+ test cases across all three components
- Hard test cases (boundary, error, integration)
- Property-based tests where applicable
- Real-world scenarios from FRD

**Verifier:**
- Run all tests with pytest
- Capture coverage reports
- Verify all AC met

---

## Rollback Plan

**Trigger:** Any task fails GATE 4 (test coverage review)

**Procedure:**
1. Delete component files (compressor.py, arch_retrieval.py, model_adapter.py)
2. Delete test files
3. Revert __init__.py exports
4. Revert PHASE_4_BUILD_PLAN.md markers
5. Git reset --hard HEAD~N (to before feature branch)

**Verification:**
- Codebase returns to Phase 4 state (components 1–3 only)
- Tests still pass for components 1–3
- PHASE_4_BUILD_PLAN.md shows only 3/9 complete

---

## Success Metrics

- ✅ All 3 components built and tested
- ✅ 50+ test cases across components (20+ per component avg)
- ✅ 100% test pass rate
- ✅ Code review clean (no critical issues)
- ✅ No external API calls in tests (all mocked)
- ✅ Edge cases covered (empty, null, max, min, invalid)
- ✅ Integration tests with Phase 4 pipeline (deduplicator → reranker → graph expander → compressor)
