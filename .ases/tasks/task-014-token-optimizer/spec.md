# Task-014: Token Optimizer (Pillar 5) — Specification

**Phase:** Phase 3 (Execution) — Week 19–20  
**Objective:** Implement context assembly and token budget management; unblock WorkflowExecutor; satisfy FRD Pillar 5 §10 mandate  
**Scope:** 5 atomic tasks (TokenBudget, ContextChunk/ContextPackage, assembler, prompt assembly, package scaffolding)  
**Out of Scope:** Semantic reranking, dedup, graph expansion, architecture-aware weighting, compression, model adapters, quality logging (defer to task-015)

---

## Specification Refinements (GATE 1 Approval)

Per human feedback during GATE 1 PLANNER review, the following three critical behaviors have been explicitly defined:

### 1. Deterministic Tie-Breaking
- When artifacts share identical `relevance_score`, secondary sort applies: (1) `token_count` ascending (prefer smaller), (2) `artifact.id` ascending (lexicographic).
- Identical inputs guarantee identical output (no hash-order dependencies, no randomness).
- Prompt chunk ordering is also deterministic: by `chunk.id` ascending (independent of ContextPackage order).

### 2. TokenBudget Ownership
- `TokenBudget` is **mutable by design.** Passed instance is **modified in place** by `assemble_context()` (increments `used`).
- Caller is responsible for budget lifecycle: create fresh per step, or explicitly reset `used` between calls.
- ContextPackage returns reference to same budget instance (not a copy) for traceability.
- No thread-safety guarantees; caller must ensure per-thread or per-step budget instances.

### 3. Prompt Assembly Contract
- **Ordering:** Chunks ordered by `chunk.id` ascending (deterministic, independent of assembly order).
- **Format:** `\n\n--- [{source_type}:{source_id}] ---\n{content}\n` per chunk (fixed delimiter, no escaping).
- **Duplicates:** Multiple chunks with same `source_id` are all included (no de-duplication).
- **Length Limit:** None enforced by assembler (passive layer). LLM client enforces max_tokens downstream.

These refinements ensure deterministic behavior, clear ownership semantics, and uniform documentation across all implementation modules.

---

## Acceptance Criteria

### AC1: TokenBudget Implementation
- `TokenBudget` dataclass exists at `packages/token-optimizer/src/token_optimizer/budget.py`
- Fields: `total: int`, `used: int`, `model: str` (per FRD §10)
- Property: `remaining: int` returns `total - used`
- Method: `can_fit(tokens: int) -> bool` returns `tokens <= remaining`
- Method: `consume(tokens: int) -> None` increments `used` by `tokens` or raises `BudgetExceededError` if `used + tokens > total`
- `BudgetExceededError` exception class exists and is raised with meaningful message

### AC2: ContextChunk and ContextPackage Types
- `ContextChunk` dataclass at `packages/token-optimizer/src/token_optimizer/types.py`
  - Fields: `id: str`, `source_type: str` (one of "symbol"|"artifact"|"git"|"architecture"), `source_id: str`, `content: str`, `relevance_score: float`, `token_count: int`, `included: bool`
- `ContextPackage` dataclass at same location
  - Fields: `id: str`, `workflow_run_id: str`, `step_id: str`, `chunks: list[ContextChunk]`, `budget: TokenBudget`, `assembled_at: str` (ISO datetime)
- Both classes importable via `packages.token_optimizer.types`

### AC3: Context Assembler
- `assemble_context` function exists at `packages/token-optimizer/src/token_optimizer/assembler.py`
- Signature: `assemble_context(query: str, repo_id: str, artifact_store: Any, budget: TokenBudget, step_id: str, workflow_run_id: str, model: str = "claude") -> ContextPackage`
- **Deterministic Tie-Breaking:** When artifacts have identical `relevance_score`, sort secondarily by (1) ascending `token_count` (prefer smaller chunks), then (2) ascending `artifact.id` (lexicographic, stable). This ensures identical inputs always produce identical context packages.
- **Budget Ownership:** The passed `budget: TokenBudget` instance is mutable and **intentionally modified in place**. Each call to `assemble_context()` increments `budget.used` for every included chunk. Callers must pass a fresh or reset budget per assembly step, or manage state explicitly. Returns the same budget instance within the ContextPackage for traceability.
- Behavior:
  - Calls `artifact_store.search(query)` (or appropriate search method) to get candidate `Artifact`s
  - Converts each `Artifact` to a `ContextChunk` with `token_count = artifact.estimated_tokens`
  - Sorts chunks descending by `relevance_score`, then ascending by `token_count`, then ascending by `artifact.id` (deterministic)
  - Greedily includes chunks while `budget.can_fit(chunk.token_count)`, calling `budget.consume()` per included chunk (modifies budget in place)
  - Sets `included=True` for included chunks, `False` for remainder (never silently drops chunks)
  - Returns `ContextPackage` with all chunks (included and excluded), final budget state (budget.used incremented), UUID id, and current timestamp

### AC4: Prompt Assembler
- `assemble_prompt` function exists at `packages/token-optimizer/src/token_optimizer/prompt.py`
- Signature: `assemble_prompt(context_package: ContextPackage, step: ExecutionStep, agent: Any, skills: list[Any]) -> tuple[str, str]`
- Returns: `(system_prompt, user_message)` tuple
- **System Prompt:** Concatenates agent.system_prompt + skill prompts (per existing `step_runner._assemble_system_prompt` logic, unchanged).
- **User Message Contract:**
  - Includes only chunks where `chunk.included=True` (respects budget decisions)
  - Chunk ordering: ascending by `chunk.id` (lexicographic, deterministic)
  - Format per chunk: `\n\n--- [{source_type}:{source_id}] ---\n{content}\n` (triple-dash delimiter, content verbatim)
  - Separator between chunks: blank line (`\n\n`) already present in format
  - If multiple chunks share the same `source_id`: include all (no dedup); order by chunk.id as tie-breaker
  - Maximum prompt length: no hard limit applied (assembler is passive; LLM client enforces max_tokens). If a future caller needs truncation, it occurs at LLM call time, not in assembler.
- Replaces the stub at `step_runner.py:151-160`

### AC5: WorkflowExecutor Integration
- `workflow_executor.py:118` changed from `context_package=None` to a real call to `assemble_context(...)`
- Before calling `run_step`, executor now:
  1. Creates or receives a `TokenBudget` (either from plan metadata or defaults to `total=8192` for Claude)
  2. Calls `assemble_context(step.step_id, repo_id, artifact_store, budget, step.step_id, run_id)`
  3. Passes the real `ContextPackage` to `run_step`
- `step_runner.run_step` calls new `assemble_prompt(context_package, ...)` instead of stub
- Integration test confirms end-to-end: `run_step` receives a real context package with both included and excluded chunks

### AC6: Broken Import Fixed
- `apps/api_server/src/routers/orchestration.py` import line changed from `from packages.shared.types import TokenBudget` to `from packages.token_optimizer.budget import TokenBudget`
- Import resolves without error (no circular dep verification at this stage, ARCHITECT handles that)

### AC7: Package Exports
- `packages/token_optimizer/src/token_optimizer/__init__.py` exports: `TokenBudget`, `BudgetExceededError`, `ContextChunk`, `ContextPackage`, `assemble_context`, `assemble_prompt`
- `pyproject.toml` has correct package declaration and workspace path dependencies on orchestration/context-hub

### AC8: Zero Regressions
- All existing tests in `packages/orchestration/tests/` pass unchanged (27+ selector tests, 10+ executor tests, 5+ evidence tests)
- All existing tests in `packages/context-hub/tests/` pass unchanged (54+ tests per CLAUDE.md)
- All existing tests in other packages pass unchanged (repo-intelligence 85+, arch-intelligence 76+, impact-analysis 42+)
- Total baseline: 455+ passing tests remain passing

---

## Expected Test Metrics

| Category | Count | Notes |
|----------|-------|-------|
| Unit tests | 20+ | budget arithmetic/overflow, chunk sorting, prompt assembly, type validation |
| Integration tests | 8+ | assembler + real ArtifactStore, executor + assembler end-to-end |
| Edge cases | 6+ | empty artifact set, budget=0, single chunk > budget, exact-fit boundary, null chunks |
| Property-based | 1+ | hypothesis: `sum(chunk.token_count for c in pkg.chunks if c.included) <= budget.total`, ≥10 generated cases |
| Real-repo | 1+ | real SQLite `ArtifactStore` (not mocks), real artifact data from context-hub schema |
| **Total** | **35+** | **≥85% coverage, 100% pass rate** |

---

## Files to Create

```
packages/token-optimizer/
  src/
    token_optimizer/
      __init__.py                    (exports)
      budget.py                      (TokenBudget, BudgetExceededError)
      types.py                       (ContextChunk, ContextPackage)
      assembler.py                   (assemble_context)
      prompt.py                      (assemble_prompt)
  tests/
    test_budget.py                   (unit: budget math, overflow, edge cases)
    test_types.py                    (unit: type construction, validation)
    test_assembler.py                (unit + integration: artifact search, chunk conversion, greedy inclusion)
    test_prompt.py                   (unit: prompt assembly from chunks)
    test_integration.py              (integration: executor + assembler end-to-end)
  pyproject.toml                     (already exists; update with deps)
```

---

## Files to Modify (Outside token-optimizer)

1. **`packages/orchestration/src/executor/workflow_executor.py`** (line 118)
   - Replace `context_package=None` with real call to `assemble_context(...)`
   - Import `assemble_context` from token_optimizer

2. **`packages/orchestration/src/executor/step_runner.py`** (line 151-160)
   - Replace `_assemble_user_message` stub with call to `assemble_prompt(...)`
   - Import `assemble_prompt` from token_optimizer

3. **`apps/api_server/src/routers/orchestration.py`** (import line)
   - Change `from packages.shared.types import TokenBudget` → `from packages.token_optimizer.budget import TokenBudget`

---

## Determinism and Ownership Invariants

### Deterministic Behavior
- **Identical Input → Identical Output:** All token-optimizer functions must be deterministic. Given the same `query`, `repo_id`, `artifact_store` state, `budget` (total/used/model), `step_id`, `workflow_run_id`, multiple calls must produce context packages with identical chunk ordering, included/excluded status, and prompt text.
- **Tie-Breaking:** When artifacts share the same `relevance_score`, secondary sort by `token_count` (ascending), then by `artifact.id` (lexicographic ascending). No randomness, no hash-order dependencies, no insertion-order variations.
- **Prompt Chunk Ordering:** Chunks in the user message are ordered by `chunk.id` ascending (lexicographic). This is independent of their order in the ContextPackage, ensuring prompt text is deterministic.

### Budget Ownership
- `TokenBudget` is **mutable by design.** `assemble_context()` intentionally modifies the passed `budget` instance (increments `budget.used`).
- **Caller Responsibility:** Each orchestration step must either (a) create a fresh budget, or (b) explicitly reset `budget.used = 0` between calls. Token-optimizer does not manage budget lifecycle; it only enforces the ceiling.
- **Return Value:** The ContextPackage returns a reference to the same budget instance (not a copy), so callers can inspect final `budget.used` for telemetry/logging.
- **Thread Safety:** If multiple threads call `assemble_context()` concurrently with the same budget instance, the behavior is undefined (no locking). Callers must ensure per-thread or per-step budget instances.

### Prompt Assembly Determinism
- Chunk ordering in the final prompt is **always by chunk.id ascending,** independent of inclusion order in the ContextPackage.
- Format is fixed: `\n\n--- [{source_type}:{source_id}] ---\n{content}\n` for every chunk, no variations.
- Duplicate source IDs are not de-duplicated; all chunks are included if `included=True`.

---

## Input/Output Contracts

### assemble_context
**Input:**
- `query: str` — search query for artifacts (e.g., "auth middleware")
- `repo_id: str` — repository ID (for ArtifactStore filtering)
- `artifact_store: ArtifactStore` — context-hub's search interface (immutable; read-only)
- `budget: TokenBudget` — token budget (mutable; **will be modified in place** — caller must manage lifecycle)
- `step_id: str` — orchestration step ID (for traceability)
- `workflow_run_id: str` — workflow run ID (for traceability)
- `model: str` — LLM model name (stored in budget, default "claude")

**Output:**
- `ContextPackage` with:
  - All candidate chunks (both included and excluded)
  - `included=True` for greedily selected chunks (sum of their token_count ≤ budget.remaining at assembly time)
  - `included=False` for remainder (not included due to budget exhaustion or not fetched by search)
  - Final budget state (budget.used incremented by sum of included chunk token counts)
  - Budget reference: same instance passed in (not a copy)
  - UUID id, workflow_run_id, step_id, current ISO timestamp
  - Chunk ordering: as returned by artifact_store.search() (search order preserved in ContextPackage)

**Side Effects:**
- `budget.used` is incremented (mutable state change). No other arguments are modified.

**Determinism Guarantee:**
- Identical inputs (same query, repo_id, artifact_store state, budget.total/used, etc.) produce identical ContextPackage (same chunks, same included/excluded status, same total tokens used).
- Tie-breaking: relevance_score desc → token_count asc → artifact.id asc

### assemble_prompt
**Input:**
- `context_package: ContextPackage` — assembled chunks (some may have `included=False`)
- `step: ExecutionStep` — orchestration step metadata (unused; for future extensibility)
- `agent: AgentManifest` — agent definition (has system_prompt)
- `skills: list[SkillManifest]` — selected skills (each has content/system_prompt)

**Output:**
- `(system_prompt: str, user_message: str)` tuple

**System Prompt:**
- Concatenates `agent.system_prompt` + all skill prompts (per existing `step_runner._assemble_system_prompt` logic)
- Unchanged from current behavior (deterministic, no token_optimizer innovations)

**User Message:**
- **Source Chunks:** Only chunks where `chunk.included=True` are included (respects budget decisions)
- **Ordering:** Chunks are ordered by `chunk.id` ascending (lexicographic, deterministic, independent of ContextPackage order)
- **Format:** Each chunk is formatted as `\n\n--- [{source_type}:{source_id}] ---\n{content}\n`
  - Leading blank line separates from previous chunk (or system prompt if first)
  - Source type: one of "symbol"|"artifact"|"git"|"architecture" (for traceability)
  - Source ID: `chunk.source_id` (e.g., artifact UUID, symbol qualified name)
  - Content: chunk's `.content` field verbatim (no escaping, no truncation)
  - Trailing newline after content
- **Duplicate Source IDs:** If multiple chunks have the same `source_id`, all are included (no dedup). Ordered by `chunk.id` as secondary key.
- **Maximum Length:** No hard limit enforced by assembler (passive). If LLM has max_tokens constraint, truncation happens at LLM call time in step_runner, not here.
- **Empty Included Set:** If no chunks have `included=True`, user message is empty string `""`.

**Determinism Guarantee:**
- Identical input produces identical prompt text (chunk order and format are deterministic).

---

## Known Limitations (Not Built)

The following FRD Pillar 5 features are **explicitly deferred** to task-015 or later:

1. **Intent-aware reranker** — Requires embeddings/semantic similarity across chunks; context-hub's embedding provider is still a `NullEmbedding` stub (task deferred: task-015)
2. **Duplicate remover** — Requires semantic similarity detection; same blocker
3. **Graph expander** — Requires call-graph/import-graph data and symbol neighbor traversal; different issue tracking, tested separately
4. **Architecture-aware retrieval** — Requires `ArchitectureModel` weighting and subsystem scoring; scoped to future iteration
5. **Context compressor** — Requires summarization (LLM call or heuristic); out of scope
6. **Model context adapter** — Requires multi-model token counting (Claude, GPT, Gemini); only Claude supported now
7. **Context quality logger** — Logging/observability feature; low priority for Phase 3
8. **Prompt assembler (advanced)** — Only basic concatenation implemented; advanced persona/role injection deferred

These are documented in implementation-notes.md as "NOT BUILT (task-015+)" and marked in test-plan.md as known acceptable gaps.

---

## Verification Commands (VERIFIER will execute)

```bash
# Import validation
python -c "from packages.token_optimizer.budget import TokenBudget, BudgetExceededError; print('Import OK')" 2>&1 | tee .ases/evidence/task-014/import-check.log

# Pilot test (sample)
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_can_fit -v 2>&1 | tee .ases/evidence/task-014/pilot-test.log

# Full test suite
pytest packages/token-optimizer/tests/ -v --tb=short --cov=packages/token-optimizer 2>&1 | tee .ases/evidence/task-014/test-full.log
echo "EXIT: $?" >> .ases/evidence/task-014/test-full.log

# Regression: full repo test suite
pytest 2>&1 | tee .ases/evidence/task-014/regression-full.log
echo "EXIT: $?" >> .ases/evidence/task-014/regression-full.log
```

---

*End of spec.md*
