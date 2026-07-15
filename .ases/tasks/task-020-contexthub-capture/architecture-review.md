# Architecture Review — task-020-contexthub-capture

**Verdict:** APPROVED

## Layer Compliance (ADR-015 / ADR-016)
`cli-commands` is classified as **Apps** (ADR-016, explicit: "`cli-commands`
remains classified as Apps... matches ADR-015's existing Apps
definition"). ADR-015's Apps row: "Can import from: Core, Intelligence,
Storage, Shared." `context-hub` and `shared/storage` are the **Storage**
and **Shared** layers respectively — both explicitly legal for Apps to
import. This task adds `cli-commands -> context-hub -> shared.storage`,
a strict downward hop, no new ADR required.

No Intelligence-to-Intelligence import introduced (context-hub/storage
have zero Intelligence-layer imports of their own — confirmed by reading
`store.py`/`database.py` imports directly in this review: only stdlib +
`storage` + intra-package `context_hub.*`).

## Data Flow
`capture_workflow_run(scan_root, command, argument, report)` -> builds
`ArtifactIngestionRequest` -> `OrthoDatabase(scan_root).migrate()` ->
`ArtifactStore(db, repo_id=mint_repo_id(scan_root)).ingest_artifact(req)`.

This is a **new** data flow direction for `cli-commands`: previously
every command only read from the scanned repo (via `scan_repository()`)
and returned an in-memory `CliReport` — no filesystem write to the
scanned target. This task introduces the first write path
(`<scan_root>/.ortho/ortho.db`). Flagged explicitly (also called out in
plan.md/rollback-plan.md) since it's a real behavior change in kind, not
just in code size.

## Blast Radius
One new file (`workflow_capture.py`), one call added at the end of each
of 4 existing methods in `commands.py`. Zero changes to `context-hub`,
`shared/storage`, or any Intelligence/Engineering-Copilot package.

## Design Decision Worth Flagging
Per spec.md, `mint_repo_id()` (not the `"repo"` literal
`apps/cli/src/commands/context.py` currently hardcodes) must be used for
`repo_id`. This is the correct choice — the existing `context.py`
placeholder would silently merge every distinct repo a user ever scans
with `cli-commands` into one shared memory bucket, defeating the point
of per-repo engineering memory. Not fixing `context.py`'s existing
placeholder is correctly out of scope (different call site, would need
its own task since apps/cli's `ContextCommand` has different callers/
tests than `cli-commands`).

## Failure Isolation Review
Reviewed spec.md's failure-modes table: every documented failure path
(unwritable dir, corrupt DB, ingestion validation error) is required to
be caught inside `capture_workflow_run` itself and never propagate. This
is the correct boundary — `CliCommands`'s 4 public methods must remain
exactly as reliable as they are today; memory capture is additive value,
never a new way for `guardrails`/`decide`/`plan`/`refactor` to fail.

## Verdict
APPROVED — no ADR needed, ADR-015/016 layer rules explicitly permit this
import direction, blast radius is small, the one new-in-kind risk
(filesystem write to scanned target) is identified and mitigated by the
required try/except boundary.
