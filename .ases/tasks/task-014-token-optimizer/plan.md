# Task-014: Token Optimizer (Pillar 5) — ASES PLANNER Plan

## Context

FRD Pillar 5 (§10) lists 9 Phase-4 features (reranker, dedup, graph expander, budget manager,
compressor, arch-aware retrieval, model adapter, prompt assembler, quality logger) plus a
mandatory `TokenBudget` interface that the FRD says must exist since Phase 1. It was never built —
confirmed by exploration: no Python `TokenBudget`/`BudgetExceededError` exists anywhere; only a TS
interface (`shared/types/src/context.ts`) and a local test-only mock
(`packages/orchestration/tests/test_selector_engine.py:44`). `apps/api_server/src/routers/orchestration.py`
already does `from packages.shared.types import TokenBudget`, which is currently a broken import
(no such package exists).

More importantly, task-013's `WorkflowExecutor` has two explicit stubs waiting on this task:
- `executor/workflow_executor.py:118` — `context_package=None,  # Stubbed; token optimizer (task-014) provides this`
- `executor/step_runner.py:151-160` — `_assemble_user_message` returns a placeholder string instead
  of real assembled context.

Building all 9 FRD features in one task is not testable in 30-90 min atomic chunks and isn't what's
actually blocking anything right now. This plan scopes task-014 to the **vertical slice that
unblocks WorkflowExecutor and satisfies the FRD's Phase-1 mandated interface**: real `TokenBudget`,
a Python `ContextChunk`/`ContextPackage` (mirroring the existing TS shapes), a context assembler
that pulls from context-hub's `Artifact.estimated_tokens` (the only real token-count data in the
repo today), a token budget manager (hard ceiling + priority ranking — FRD's own top-listed
feature), and a prompt assembler that replaces the step_runner stub. Reranking, dedup, graph
expansion, architecture-aware weighting, compression, model adapters, and quality logging are
deferred to a follow-up task (task-015) — each depends on infrastructure (embeddings wired into
context-hub, multiple LLM model adapters) that doesn't exist yet either.

## Package: `packages/token-optimizer/`

Already registered in the workspace root `pyproject.toml:12` and has a skeleton
`pyproject.toml` (name `ortho-token-optimizer`) but no `src/` yet.

## Atomic Tasks (5)

1. **`TokenBudget` + `BudgetExceededError`** (`src/token_optimizer/budget.py`)
   - Dataclass exactly per FRD §10: `total: int, used: int, model: str`, `remaining` property,
     `can_fit(tokens) -> bool`, `consume(tokens) -> None` (raises `BudgetExceededError`).
   - This becomes the real type `SelectorEngine.build_plan`'s `token_budget: Any` param
     (`packages/orchestration/src/selector/engine.py:195,210`) and `apps/api_server`'s broken
     import should resolve to.

2. **`ContextChunk` / `ContextPackage`** (`src/token_optimizer/types.py`)
   - Python dataclasses mirroring `shared/types/src/context.ts:1-28` field-for-field:
     `ContextChunk(id, source_type, source_id, content, relevance_score, token_count, included)`,
     `ContextPackage(id, workflow_run_id, step_id, chunks, budget, assembled_at)`.

3. **Context Assembler** (`src/token_optimizer/assembler.py`)
   - `assemble_context(query: str, repo_id: str, artifact_store: ArtifactStore, budget: TokenBudget, step_id: str, workflow_run_id: str) -> ContextPackage`
   - Pulls candidate `Artifact`s via `ArtifactStore` search (context-hub, already built), converts
     each to a `ContextChunk` (`token_count` = `Artifact.estimated_tokens`), sorts deterministically:
     (1) `relevance_score` descending, (2) `token_count` ascending, (3) `artifact.id` ascending.
   - Greedily includes chunks while `budget.can_fit(chunk.token_count)`, calls `budget.consume()` per
     included chunk (modifies budget in place), marks the rest `included=False`.
   - Returns ContextPackage with all chunks (included and excluded) and final budget state.
   - **Determinism & Ownership:** Identical inputs produce identical output (deterministic tie-breaking).
     Budget is mutable and intentionally modified in place; caller must manage lifecycle (create fresh
     or reset per step). No truncation applied (LLM enforces max_tokens downstream).
   - This is the FRD's "Token budget manager" feature (hard ceiling + priority ranking) — the only
     one of the 9 listed features actually implementable now without new infra.

4. **Prompt Assembler** (`src/token_optimizer/prompt.py`)
   - `assemble_prompt(context_package: ContextPackage, step, agent, skills) -> tuple[str, str]`
     returning `(system_prompt, user_message)`.
   - **System Prompt:** Agent + skill prompts (unchanged from existing `_assemble_system_prompt` logic).
   - **User Message:** Only `included=True` chunks; ordered by `chunk.id` ascending (deterministic).
     Format: `\n\n--- [{source_type}:{source_id}] ---\n{content}\n` per chunk. Duplicate source IDs not
     de-duplicated. No hard prompt-length limit (LLM enforces max_tokens).
   - Replaces `step_runner._assemble_user_message`'s placeholder (`step_runner.py:151-160`).
   - `step_runner.run_step` updated to call this, and `workflow_executor.py:118`'s `context_package=None`
     replaced with real call to `assemble_context(...)` before `run_step`.

5. **CLI wiring + package scaffolding**
   - `packages/token-optimizer/src/token_optimizer/__init__.py` exporting the above.
   - `packages/token-optimizer/pyproject.toml` updated with actual deps (none new — stdlib only;
     depends on `context-hub` and `orchestration` as workspace path deps for the `Artifact`/
     `ExecutionStep` types it consumes).
   - No new CLI command — this wires into `ortho run`'s existing execution path
     (`WorkflowExecutor.execute`), not a user-facing surface.

## Files to Modify (outside the new package)
- `packages/orchestration/src/executor/workflow_executor.py` (line 118: real context_package call)
- `packages/orchestration/src/executor/step_runner.py` (`_assemble_user_message` → real assembler)
- `apps/api_server/src/routers/orchestration.py` (fix broken `TokenBudget` import to point at
  `packages.token_optimizer.budget`)

## Files to NOT Touch
- `shared/types/src/context.ts` (TS interface already correct, no changes needed)
- context-hub's embedding provider (`NullEmbedding` stub) — semantic search/embeddings are out of
  scope; task-014 uses context-hub's existing BM25/keyword search + `estimated_tokens`, not vectors
- Reranking, dedup, graph expansion, compression, model adapters, quality logger — deferred to
  task-015 (documented as "NOT built" in implementation-notes.md, not silently dropped)

## Acceptance Criteria
- AC1: `TokenBudget.can_fit()`/`consume()` behave per FRD §10 spec exactly (including raising
  `BudgetExceededError` on overflow). Budget is mutable; `consume()` increments `used` in place.
- AC2: `assemble_context()` deterministically returns identical ContextPackage for identical inputs.
  Total included chunk tokens never exceeds `budget.total`. Tie-breaking: `relevance_score` desc →
  `token_count` asc → `artifact.id` asc. Identical inputs produce identical chunk order and
  included/excluded status.
- AC3: `assemble_context()` prioritizes higher `relevance_score` chunks. When budget exhausted,
  lower-relevance chunks marked `included=False` (not silently dropped). All candidate chunks
  returned in ContextPackage (included and excluded).
- AC4: `assemble_prompt()` deterministically produces identical user message for identical input.
  Chunks ordered by `chunk.id` ascending (independent of ContextPackage order). Format:
  `\n\n--- [{source_type}:{source_id}] ---\n{content}\n` per chunk. Only `included=True` chunks
  included in final message.
- AC5: `WorkflowExecutor.execute()` no longer passes `context_package=None` — integration test
  confirms `run_step` receives real `ContextPackage` from `assemble_context()`.
- AC6: Zero regressions in existing orchestration/context-hub test suites (455+ tests per CLAUDE.md
  baseline).

## Expected Test Metrics
- Unit: 20+ (budget arithmetic/overflow, chunk sorting, prompt assembly)
- Integration: 8+ (assembler + real ArtifactStore, executor + real assembler end-to-end)
- Edge cases: 6+ (empty artifact set, budget=0, single chunk exceeding budget, exact-fit boundary)
- Property-based: 1+ (hypothesis: assembled package total tokens always ≤ budget.total, ≥10 cases)
- Real-repo: 1+ (uses an actual `ArtifactStore` against a real SQLite db, not mocks)
- Total: 35+, coverage ≥85%, pass rate 100%

## Risks
- **Risk:** `ArtifactStore` has no full-text/relevance search wired for arbitrary queries beyond
  what context-hub's BM25/FTS5 already does.
  **Mitigation:** Reuse context-hub's existing search path as-is (already built, task-007/010); no
  new search logic in token-optimizer, only consumption of its output.
- **Risk:** Scope creep back toward all 9 FRD features.
  **Mitigation:** implementation-notes.md explicitly lists the other 8 as "not built, task-015".

## Rollback Plan
- Local (uncommitted): `git reset --hard` to pre-task-014 commit (3f2a59e).
- Published: `git revert` the task-014 commit(s); `workflow_executor.py`/`step_runner.py` changes
  revert cleanly back to the `context_package=None` stub since no other code depends on the new
  behavior yet (WorkflowExecutor is not yet wired into a shipped CLI path).
- Trigger: regression in orchestration test suite, or `ortho run` integration breaks.

## Next Steps After This Plan Is Approved
Per ASES: this is GATE 1 (PLANNER). Next is ARCHITECT session (GATE 2) — architecture-review.md +
possible ADR (new package `token-optimizer` gets real content for the first time, and it takes a
dependency on `context-hub`/`orchestration`, which ARCHITECT should validate doesn't create a
circular import: orchestration → token-optimizer → context-hub, no cycle back to orchestration).
