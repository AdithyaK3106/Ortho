# Plan — task-020-contexthub-capture

## Goal
Every `CliCommands` call (`guardrails`, `decide`, `plan`, `refactor`) logs
its invocation and findings into ContextHub as a real `workflow_run`
artifact, so ortho starts accumulating genuine "engineering memory"
across runs — the core thesis of the vNext strategy (this is the last of
the three items explicitly authorized this session: "2. ContextHub memory
capture (the actual moat)", ordered last per the user's "3 -> 4 -> 2"
build order).

## Current State
- ContextHub (`packages/context-hub`) already has a fully real, tested
  API: `ArtifactStore.ingest_artifact(ArtifactIngestionRequest)` persists
  to SQLite with automatic FTS5 sync (schema.py, store.py — both
  pre-existing, untouched by tasks 017/018/019).
- A real precedent for wiring `OrthoDatabase` + `ArtifactStore` already
  exists: `apps/cli/src/commands/context.py`'s `ContextCommand.add()`
  (`db = OrthoDatabase(root); db.migrate(); store = ArtifactStore(db,
  repo_id=...)`), and `mint_repo_id()` (repo-intelligence/index_store.py)
  gives a stable, deterministic repo_id already used elsewhere
  (`workflow_cli.py`'s `_open_db`).
- `CliCommands` (packages/cli-commands) currently has **zero** ContextHub
  integration — every call to `guardrails()`/`decide()`/`plan()`/
  `refactor()` is stateless; nothing persists after the process exits.
- `ARTIFACT_TYPES` (ingestion.py) already includes `"workflow_run"` —
  no schema/validation change needed.

## Scope
Add a single new internal helper, `_capture_workflow_run()`, called at
the end of each of the four `CliCommands` methods (both success and
failure paths), which:
1. Builds an `ArtifactIngestionRequest(type="workflow_run", title=...,
   content=..., source="cli", relevance_scope="project", tags=[...])`
   summarizing: which command ran, the intent/path argument, success/
   failure, and a short excerpt of `CliReport.content` (findings/errors).
2. Opens `OrthoDatabase(scan_target_or_cwd)`, calls `.migrate()`,
   constructs `ArtifactStore(db, repo_id=mint_repo_id(scan_target))`
   (same minting scheme `workflow_cli.py`/`index_store.py` already use —
   NOT the placeholder literal `"repo"` `context.py` currently uses,
   since that would silently merge every scanned repo's history into one
   shared bucket).
3. Calls `store.ingest_artifact(req)`.
4. **Never raises.** Wrapped in `try/except Exception: logging.warning(...)`
   — matches `ArtifactStore._compute_embedding_async`'s own existing
   "log and swallow" discipline for non-critical background writes.
   Memory capture failing must never cause a `guardrails`/`decide`/
   `plan`/`refactor` call that otherwise succeeded to report failure.

## What Gets Captured (per call)
- Command name (`guardrails`/`decide`/`plan`/`refactor`).
- The raw intent/path argument as given.
- `CliReport.success`.
- A bounded excerpt of `CliReport.content` (first N lines/chars — full
  violation dumps on large repos could be enormous; excerpt keeps
  artifacts queryable rather than dominated by one giant blob).
- Timestamp (via `ArtifactIngestionRequest`'s own `created_at`, set
  internally by `ArtifactStore.ingest_artifact`; task-020 does not
  duplicate this).

## Out of Scope
- Building a `context.py`-style CLI surface for *querying* captured
  workflow runs (e.g. "ortho history", "ortho memory search") — this
  task is capture-only. Querying is real future work, explicitly noted
  as a candidate follow-up, but adding a query UX now would be scope
  creep beyond "start accumulating memory."
- Changing `ARTIFACT_TYPES`/schema — `workflow_run` already exists.
- Retrofitting `apps/cli/src/commands/context.py`'s `repo_id="repo"`
  placeholder — out of this task's blast radius (different package,
  different call site, pre-existing behavior).
- Embeddings/semantic search over captured runs — `NullEmbedding` is the
  existing default; no change needed or in scope.

## Acceptance Criteria
1. After any of the 4 commands runs (success or failure), a real
   `workflow_run` artifact is queryable via `ArtifactStore.get_artifact`/
   BM25 search against the same repo's `.ortho/ortho.db`.
2. Capture failure (e.g. read-only filesystem, corrupt DB) never flips
   an otherwise-successful `CliReport.success` to `False`, and never
   raises out of the public `CliCommands` method.
3. Two different repos scanned in the same test session get two
   different, stable `repo_id`s (no cross-repo memory bleed).
4. Existing `guardrails()`/`decide()`/`plan()`/`refactor()` behavior
   (return values, content) is otherwise byte-for-byte unchanged —
   capture is a side effect, not a behavior change.
5. mypy --strict introduces zero new type-correctness errors.
6. Real-repo verification: run all 4 commands against `repos/click`,
   confirm 4 real rows land in that repo's `.ortho/ortho.db`.
