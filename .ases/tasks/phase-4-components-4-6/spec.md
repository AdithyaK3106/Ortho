# Specification: Phase 4 Components 4–6

**Task ID:** phase-4-components-4-6  
**Reference:** PHASE_4_BUILD_PLAN.md sections 4–6, FRD §10  
**Contracts:** Per component below  

---

## Component 4: Context Compressor

**Purpose:** When context exceeds token budget, summarize low-priority chunks instead of discarding them.

### Interface

```python
def compress_over_budget(
    context_package: ContextPackage,
    compression_target: float = 0.6,  # Keep 60% of text, drop 40%
    summarization_model: str = "claude-haiku-4-5-20251001",
) -> ContextPackage:
    """
    Compress context package to fit budget.
    
    Args:
        context_package: Output from assemble_context()
        compression_target: Target compression ratio (0.0–1.0)
        summarization_model: LLM model string
    
    Returns:
        New ContextPackage with compressed content
    """
```

### Behavior

- Input: ContextPackage with chunks (mixed `included=True/False`)
- Algorithm:
  1. Identify chunks with `included=False` (already decided as low-priority)
  2. Group by `source_type` (artifact, symbol, git, architecture)
  3. For each group, call summarization model (max 3 retries)
  4. Replace `chunk.content` with summary
  5. Recompute `chunk.token_count` via tiktoken
  6. Re-run greedy packing to fit budget
  7. Return modified ContextPackage
- Prompt template: "Summarize this {source_type} in {compression_target}% of tokens, preserving key facts."
- Caching: By chunk.id (deterministic hashing)
- Fallback: On API error, return uncompressed (skip chunk)

### Test Coverage (15+ cases)

| Case | Input | Expected | Notes |
|------|-------|----------|-------|
| Over budget | 15K tokens, 8K budget | Fit budget | Normal path |
| Exact fit | 8K tokens, 8K budget | No compression | Early exit |
| Empty package | 0 chunks | 0 chunks returned | Edge case |
| All included | All `included=True` | No compression | Skip low-priority |
| All excluded | All `included=False` | All compressed | Max compression |
| Single large | 1×12K token chunk | Compressed to ~7K | Verify reduction |
| Multiple groups | 5 artifact + 5 symbol | All groups compressed | Verify per-group |
| API timeout | Network error | Fallback (uncompressed) | Error handling |
| API rate limit | 429 response | Retry 3x, then skip | Retry logic |
| Invalid model | "unknown-model" | Raise ValueError | Config error |
| Compression target 0 | target=0.0 | Keep 0% (minimal) | Edge case |
| Compression target 1 | target=1.0 | Keep 100% (no compression) | Edge case |
| Token count accuracy | Verify tiktoken | Counts match | Correctness |
| Deterministic | Same input 2x | Same summary | Caching |
| Large batch | 100 chunks | Process all | Performance |

---

## Component 5: Architecture-Aware Retrieval

**Purpose:** Weight chunks by architectural centrality.

### Interface

```python
def boost_by_architecture(
    chunks: list[ContextChunk],
    architecture_model: ArchitectureModel | None,
    centrality_weights: dict[str, dict[str, float]] | None = None,
) -> list[ContextChunk]:
    """
    Boost relevance scores for architecturally central chunks.
    
    Args:
        chunks: Candidate chunks
        architecture_model: ArchitectureModel from arch-intelligence (or None)
        centrality_weights: Config per style (uses defaults if None)
    
    Returns:
        Same chunks, relevance_score boosted, resorted
    """
```

### Behavior

- Input: Chunks + ArchitectureModel (or None)
- Algorithm:
  1. If arch_model is None, return chunks unchanged
  2. For each chunk, extract `source_id` (symbol or file)
  3. Look up source in architecture_model (layers, subsystems)
  4. If found in central layer (e.g., "service" in layered arch):
     - Multiply `relevance_score` by centrality_weight (1.5x)
  5. If found in low-coupling subsystem:
     - Multiply by subsystem boost (1.2x)
  6. Apply max of layer boost and subsystem boost (not cumulative)
  7. Re-sort by relevance_score descending, chunk.id for ties
  8. Return modified chunks

### Default Centrality Weights

```python
{
    "layered": {
        "service": 1.5,      # Core business logic
        "domain": 1.4,       # Domain models
        "data": 1.3,         # Data access
        "presentation": 1.0, # UI/API (not central)
    },
    "microservices": {
        "high_coupling": 1.0,   # Not central
        "low_coupling": 1.3,    # Central (independent)
    },
    "hexagonal": {
        "domain": 1.5,      # Core
        "adapter": 1.2,     # Supporting
        "port": 1.1,        # Interface
    },
    "flat": {},  # No boost (all equal)
}
```

### Test Coverage (12+ cases)

| Case | Arch Style | Expected | Notes |
|------|-----------|----------|-------|
| Layered, central | service layer | 1.5x boost | Normal path |
| Layered, peripheral | presentation layer | 1.0x | No boost |
| Microservices, low-coupling | independent svc | 1.3x boost | Normal |
| Microservices, high-coupling | tightly coupled | 1.0x | No boost |
| Hexagonal, domain | core domain | 1.5x boost | Normal |
| Hexagonal, adapter | supporting adapter | 1.2x boost | Normal |
| Flat arch | any module | 1.0x | No boost (flat has none) |
| No arch model | None | Original scores | Early exit |
| Empty chunks | 0 chunks | 0 chunks | Edge case |
| Symbol not found | Unknown symbol | 1.0x (no boost) | Fallback |
| Resorted correctly | Mixed scores | Descending order | Verify sort |
| Tie-breaking | Identical scores | By chunk.id | Deterministic |

---

## Component 6: Model Context Adapter

**Purpose:** Adjust prompt format and content per LLM model.

### Interface

```python
def adapt_prompt_for_model(
    system_prompt: str,
    user_message: str,
    model: str,
) -> tuple[str, str]:
    """
    Adapt prompt format and content for specific model.
    
    Args:
        system_prompt: Original system prompt
        user_message: Original user message
        model: Model identifier (e.g., 'claude-opus-4-8')
    
    Returns:
        (adapted_system_prompt, adapted_user_message)
    """
```

### Behavior

- Input: System prompt, user message, model identifier
- Algorithm per model:
  - **claude-opus-4-8**: Identity (return unchanged)
  - **claude-haiku-4-5-\***: Remove verbose sections, prioritize essentials
    - Remove explanatory text >200 words
    - Keep only first 2 paragraphs of system prompt
    - Keep all user message
  - **gpt-4\*** (all GPT-4 variants): Adjust system prompt format
    - GPT uses different token counting (fewer tokens per word)
    - Add "Be concise." reminder
  - **gpt-4o**: Similar to GPT-4 + add "Use JSON output if applicable"
  - **Unknown model**: Identity (fallback to no change)
- All transformations deterministic and text-based (no ML)
- Comment all rules with model-specific reasoning

### Test Coverage (10+ cases)

| Case | Model | Expected | Notes |
|------|-------|----------|-------|
| Opus | claude-opus-4-8 | Identity | No change |
| Haiku verbose | claude-haiku-4-5 | Shortened | Remove verbose |
| Haiku concise | claude-haiku-4-5 | Minimal change | Already short |
| GPT-4 | gpt-4 | Format adjusted | Add conciseness |
| GPT-4-turbo | gpt-4-turbo-preview | Format adjusted | Same as GPT-4 |
| GPT-4o | gpt-4o | Format + JSON hint | Specific variant |
| Unknown model | custom-model-v1 | Identity | Fallback |
| Empty prompts | system="", user="" | Empty returned | Edge case |
| Very long | 5000 char system | Truncated for Haiku | Compression |
| Special chars | System with `\n\t` | Preserved correctly | Format safety |

---

## Integration Points

All three components fit into Phase 4 pipeline:

```
[Query] 
  → expand_by_call_graph() [component 3]
  → retrieve_chunks()
  → detect_and_remove_duplicates() [component 1]
  → rerank_by_intent() [component 2]
  → boost_by_architecture() [component 5] ← NEW
  → assemble_context()
  → compress_over_budget() [component 4] ← NEW
  → adapt_prompt_for_model() [component 6] ← NEW
  → prompt_assembler()
  → LLM
```

---

## Acceptance Criteria (GATE 4 requirements)

- [ ] 50+ test cases across all 3 components
- [ ] 100% test pass rate (pytest -v)
- [ ] No external API calls in tests (all mocked)
- [ ] Edge cases documented (empty, null, boundary)
- [ ] Integration tests with real ContextPackage objects
- [ ] Type annotations complete (mypy --strict passes)
- [ ] No TODO comments (all complete)
- [ ] Code review ready (follows ponytail principles)
