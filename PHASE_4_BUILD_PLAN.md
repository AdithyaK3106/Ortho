# Phase 4 Build Plan — Token Optimizer Completion

**Objective:** Complete all 9 missing Phase 4 components to achieve FRD compliance  
**Timeline:** 17–23 days  
**Status:** Ready to start  
**Baseline:** 45-repo benchmark suite (see TASK_015_ACCEPTANCE_GAP.md)  

---

## Component Build Order & Specifications

Each component has: Description, Interface Contract, Tests, Effort estimate.

---

### 1. Semantic Duplicate Detector

**What it does:** Detects semantically overlapping context chunks; removes redundancy before token budgeting.

**When it runs:** After `assemble_context()` retrieves candidate chunks, before greedy packing.

**Interface:**

```python
def detect_and_remove_duplicates(
    chunks: list[ContextChunk],
    similarity_threshold: float = 0.85,  # Jaccard or cosine similarity
) -> list[ContextChunk]:
    """
    Remove semantically duplicate chunks from list.
    
    Strategy:
    - Compute pairwise similarity (embedding cosine or BM25-based)
    - Cluster chunks with similarity > threshold
    - Keep highest-relevance chunk per cluster; discard others
    - Return deduplicated list in original order
    
    Args:
        chunks: List of ContextChunk objects
        similarity_threshold: Similarity cutoff for deduplication (0.0–1.0)
    
    Returns:
        Deduplicated list (subset of input, same order)
    """
```

**Implementation notes:**
- Reuse sqlite-vec embeddings if available (from ContextHub)
- Fallback to simple BM25 overlap (token-level Jaccard)
- Deterministic: same input → same output ordering

**Tests:**
- 100% duplicate chunks → returns 1 chunk
- 0% overlap → returns all chunks
- Mixed: 10 chunks, 3 clusters → returns 3 representatives
- Order preservation (deduplicated list matches input order)

**Effort:** 1–2 days

---

### 2. Intent-Aware Reranker

**What it does:** Rescore context chunks by relevance to the user's intent, not just raw BM25/embedding scores.

**When it runs:** After deduplication, before greedy packing. Modifies `chunk.relevance_score`.

**Interface:**

```python
def rerank_by_intent(
    chunks: list[ContextChunk],
    intent: str,  # e.g., "implement feature X"
    intent_class: str,  # e.g., "feature_development"
) -> list[ContextChunk]:
    """
    Rerank chunks based on intent relevance.
    
    Strategy:
    - Parse intent keywords (feature, bug fix, refactor, analysis, etc.)
    - Boost scores for chunks relevant to intent class:
      - feature_development: boost "public API", "interface", "examples"
      - bug_fix: boost "error handling", "edge cases", "tests"
      - refactor: boost "dependencies", "metrics", "coupling"
      - analysis: boost "architecture", "metrics", "summary"
    - Multiply chunk.relevance_score by intent_boost_factor (1.0–2.0)
    - Resort by new relevance_score (descending)
    
    Args:
        chunks: Already deduplicated chunks
        intent: User's raw intent string
        intent_class: Output from intent router (feature_development, bug_fix, etc.)
    
    Returns:
        Same chunks, relevance_score modified, resort by score descending
    """
```

**Implementation notes:**
- Intent boosts are static rules (defined per intent class in config)
- No ML required; simple keyword matching + multipliers
- Deterministic: same input → same reranking

**Tests:**
- feature_development intent boosts API/interface chunks
- bug_fix intent boosts tests/error handling
- analysis intent boosts architecture chunks
- Non-matching chunks get 1.0x multiplier (no change)
- Resort stability (ties broken by chunk.id)

**Effort:** 2–3 days

---

### 3. Graph Expander

**What it does:** When assembling context for a task, pull related symbols via call graph.

**When it runs:** During context request building, *before* retrieval. Expands query with graph neighbors.

**Interface:**

```python
def expand_by_call_graph(
    query: str,
    repo_id: str,
    call_graph,  # CallGraph (from repo-intelligence)
    depth: int = 2,  # Number of hops to follow
    max_additions: int = 20,  # Cap on how many symbols to add
) -> list[str]:
    """
    Expand query by finding related symbols in call graph.
    
    Strategy:
    - Parse query to extract symbol names or module names
    - For each symbol in call_graph:
      - If symbol name appears in query, collect callers and callees
      - Traverse up to `depth` hops
      - Add top `max_additions` related symbols to query
    - Return expanded query as combined text
    
    Args:
        query: Original search query
        repo_id: Repository ID
        call_graph: CallGraph object from repo-intelligence
        depth: Graph traversal depth
        max_additions: Max symbols to add
    
    Returns:
        Expanded query string (original + related symbols)
    """
```

**Implementation notes:**
- Reuse existing `CallGraph` from repo-intelligence (`packages/repo-intelligence/src/call_graph.py`)
- BFS traversal up to depth N
- Deterministic ordering (sort by centrality score)

**Tests:**
- Query "authenticate user" → adds "hash password", "validate token", etc.
- Depth=0 → returns original query
- Depth=2 → reaches transitive calls
- max_additions cap prevents explosion

**Effort:** 2 days

---

### 4. Context Compressor

**What it does:** When context exceeds token budget, summarize low-priority chunks instead of discarding them.

**When it runs:** After greedy packing, if budget exceeded. Summarizes chunks marked `included=False`.

**Interface:**

```python
def compress_over_budget(
    context_package: ContextPackage,
    compression_target: float = 0.6,  # Keep 60% of text, drop 40%
    summarization_model: str = "claude-haiku",  # Fast LLM for summaries
) -> ContextPackage:
    """
    Compress context package to fit budget.
    
    Strategy:
    - Identify chunks NOT included (lowest relevance)
    - Group by source type (artifact, symbol, etc.)
    - For each group, call summarization model (locally or via API)
      - Prompt: "Summarize this code/artifact in 25% of original tokens"
    - Replace chunk.content with summary
    - Recompute chunk.token_count
    - Re-run greedy packing to fit budget
    
    Args:
        context_package: Output from assemble_context()
        compression_target: Target compression ratio (0.0–1.0)
        summarization_model: LLM to use for summarization
    
    Returns:
        New ContextPackage with compressed content, adjusted token counts
    """
```

**Implementation notes:**
- Use Anthropic API (claude-haiku for cost efficiency)
- Only compress `included=False` chunks (already decided as low-priority)
- Deterministic: same input → same summaries (cache by chunk.id)
- Token count recompute: estimate via tiktoken

**Tests:**
- Over-budget package (15K tokens, 8K budget) → compressed to fit budget
- Summaries are shorter (verify token count reduction)
- High-priority chunks (included=True) unchanged
- Compression preserves meaning (qualitative spot-check)

**Effort:** 2–3 days

---

### 5. Architecture-Aware Retrieval

**What it does:** Weight architecturally central modules higher during context retrieval.

**When it runs:** During context assembly. Boosts `chunk.relevance_score` for central symbols.

**Interface:**

```python
def boost_by_architecture(
    chunks: list[ContextChunk],
    architecture_model,  # ArchitectureModel from arch-intelligence
    centrality_weights: dict = None,  # {style: {layer: weight}}
) -> list[ContextChunk]:
    """
    Boost relevance scores for architecturally central chunks.
    
    Strategy:
    - For each chunk, identify its source symbol/file
    - Look up symbol in architecture_model
    - If in a central layer (e.g., "service" in layered arch):
      - Multiply relevance_score by centrality_weight (e.g., 1.5x)
    - If in a low-coupling subsystem:
      - Multiply by subsystem boost (e.g., 1.2x)
    - Re-sort by new score
    
    Args:
        chunks: Candidate chunks before relevance sorting
        architecture_model: ArchitectureModel from Pillar 3
        centrality_weights: Config per architecture style
    
    Returns:
        Same chunks, relevance_score boosted for central modules
    """
```

**Implementation notes:**
- Centrality weights defined in `OrthoConfig` (default provided)
- For each arch style (layered, microservices, etc.), define which layers are central
- Non-matching chunks get 1.0x (no change)

**Tests:**
- Layered arch: "service" layer boosted 1.5x vs "presentation" 1.0x
- Microservices arch: high-coupling services boosted
- Flat arch: no boost (all equal)
- Non-matching chunks unchanged

**Effort:** 2 days

---

### 6. Model Context Adapter

**What it does:** Adjust prompt assembly per LLM model (Opus vs Haiku vs GPT differences).

**When it runs:** During prompt assembly, just before returning final system/user prompt.

**Interface:**

```python
def adapt_prompt_for_model(
    system_prompt: str,
    user_message: str,
    model: str,  # "claude-opus-4-8", "claude-haiku-4-5", "gpt-4", etc.
) -> tuple[str, str]:
    """
    Adapt prompt format and content for specific model.
    
    Strategy:
    Per model, apply transformations:
    - Opus: No changes (full capability, keep all context)
    - Haiku: Remove verbose explanations; prioritize essentials
    - GPT-4: Adjust system prompt format (different token counting)
    - Local models: Add token budget warnings
    
    Args:
        system_prompt: Original system prompt
        user_message: Original user message
        model: Model identifier (from config)
    
    Returns:
        (adapted_system_prompt, adapted_user_message)
    """
```

**Implementation notes:**
- Per-model rules stored in `token_optimizer/adapters/` directory
- Rules are simple text transformations, not neural
- Fallback to identity (no change) for unknown models

**Tests:**
- Opus: no change
- Haiku: system prompt shortened, user message unchanged
- GPT-4: system prompt format adjusted
- Unknown model: identity (no change)

**Effort:** 1–2 days

---

### 7. Context Quality Logger

**What it does:** Log every context assembly decision for offline analysis and tuning.

**When it runs:** After context package is finalized. Writes to log file.

**Interface:**

```python
def log_context_quality(
    context_package: ContextPackage,
    workflow_run_id: str,
    step_id: str,
    llm_response: LLMResponse,  # After LLM call (from orchestration)
) -> None:
    """
    Log context assembly + LLM output for analysis.
    
    Logged fields:
    - timestamp
    - workflow_run_id, step_id
    - query (user intent)
    - chunks_retrieved (count)
    - chunks_included (count, after budget)
    - tokens_used / tokens_available
    - dedup_ratio (orig / dedup)
    - compression_applied (bool)
    - rerank_factor (avg)
    - architecture_boost_applied (bool)
    - model used
    - llm_input_tokens, llm_output_tokens
    - llm_stop_reason (complete, max_tokens, etc.)
    
    Output: CSV line to `ortho.log` (rotate daily)
    """
```

**Implementation notes:**
- Log to file in `.ortho/logs/context-quality.csv` (with rotation)
- Also store in SQLite `workflow_runs` table for querying
- No performance penalty (async logging)

**Tests:**
- Log file contains all expected fields
- Log entries parse as CSV
- Rotation works (new file per day)
- Sensitive data filtered (no full text content, only metadata)

**Effort:** 2 days

---

### 8. Metrics Collection + `ortho debug context` Command

**What it does:** Measure token reduction vs Phase 3 baseline; add CLI command for debugging.

**When it runs:** Post-mortem analysis; available on-demand via CLI.

**Interface:**

```python
def compute_token_metrics(
    baseline_log: str,  # Phase 3 baseline (45-repo benchmark)
    current_log: str,   # Current run logs
) -> dict:
    """
    Compare Phase 3 vs Phase 4 token usage.
    
    Metrics:
    - avg_tokens_phase3 (from baseline)
    - avg_tokens_phase4 (from current)
    - reduction_pct = (phase3 - phase4) / phase3 * 100
    - std_dev, p50, p95 (per percentile)
    
    Returns:
        {
            "reduction_pct": 15.2,
            "avg_tokens_phase3": 5200,
            "avg_tokens_phase4": 4410,
            "scenarios": {...}  # per intent class
        }
    """

def ortho_debug_context(
    intent: str,
    repo_id: str = None,  # Current repo if not provided
    verbose: bool = False,
) -> None:
    """
    CLI command: ortho debug context "<intent>"
    
    Output:
    1. Intent classification (router result + confidence)
    2. Candidate chunks retrieved (ranked by relevance)
    3. Deduplication results (before/after counts)
    4. Reranking results (relevance score changes)
    5. Budget packing (greedy algorithm trace)
    6. Compression applied (if any)
    7. Final context assembly (chunks included + token count)
    8. Estimated LLM tokens for response
    """
```

**Tests:**
- `ortho debug context "add rate limiting"` outputs full trace
- Metrics show ≥15% token reduction (goal for Phase 4)
- Per-intent breakdown available (feature, bug, refactor, analysis)
- Baseline vs current comparison accurate

**Effort:** 2 days

---

### 9. Ranking Weight Tuning Framework

**What it does:** Auto-tune reranker weights from quality logs.

**When it runs:** Offline, post-batch of runs. Updates reranker config.

**Interface:**

```python
def auto_tune_ranking_weights(
    logs: list[dict],  # Parsed context-quality.csv
    target_metric: str = "llm_quality_score",  # From LLM evaluation
) -> dict:
    """
    Auto-tune reranker intent_boost weights.
    
    Strategy:
    - Parse logs (intent_class, rerank_factor, llm_output_quality)
    - For each intent class:
      - Compute correlation between rerank_factor and quality_score
      - If correlation > 0.7, increase boost factor 10%
      - If correlation < 0.3, decrease boost factor 10%
    - Write updated config to `token_optimizer/config.toml`
    
    Args:
        logs: Parsed context quality logs
        target_metric: What to optimize for (quality, token_reduction, etc.)
    
    Returns:
        Updated weights dict (for inspection before committing)
    """
```

**Implementation notes:**
- Runs as post-batch analysis tool (not during normal operation)
- Changes small (10% increments) to avoid wild swings
- Requires human approval before committing changes
- Fallback to defaults if logs insufficient

**Tests:**
- Positive correlation → weights increase
- Negative correlation → weights decrease
- No logs → uses defaults
- Changes bounded (max 50% from baseline)

**Effort:** 1 day

---

## Implementation Sequence & Dependencies

```
Week 1:
- Component 1: Semantic Duplicate Detector (1–2 days)
- Component 2: Intent-Aware Reranker (2–3 days)

Week 2:
- Component 3: Graph Expander (2 days)
- Component 4: Context Compressor (2–3 days)

Week 3:
- Component 5: Architecture-Aware Retrieval (2 days)
- Component 6: Model Context Adapter (1–2 days)

Week 4:
- Component 7: Context Quality Logger (2 days)
- Component 8: Metrics + CLI Command (2 days)
- Component 9: Tuning Framework (1 day)

Week 4–5 (parallel):
- Integration testing
- Phase 4 exit criteria validation (≥20% token reduction)
- Final FRD compliance audit
```

---

## Success Criteria (Phase 4 Exit)

- ✅ All 9 components implemented + tested
- ✅ Token usage reduced ≥15% vs Phase 3 (measured on 45-repo baseline)
- ✅ Context quality logs available and useful (sample spot-check)
- ✅ No measurable degradation in LLM output (qualitative review of samples)
- ✅ `ortho debug context` works and provides useful trace
- ✅ All packages have tests passing (pytest)
- ✅ Type checking strict (mypy, eslint)

---

## Next Action

**Ready to start:** Begin Component 1 (Semantic Duplicate Detector) this week.

**Acceptance criteria for each component:**
1. Code written + tests pass
2. Integrated into token-optimizer package
3. Merged to main with commit message naming the component
4. Updated PHASE_4_BUILD_PLAN.md with "✅ DONE" marker

