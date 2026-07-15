# Spec — task-020-contexthub-capture

## API Contract (unchanged public signatures)
```python
def guardrails(self, path: str | None = None, **kwargs: Any) -> CliReport: ...
def decide(self, intent: str, **kwargs: Any) -> CliReport: ...
def plan(self, intent: str, **kwargs: Any) -> CliReport: ...
def refactor(self, path: str | None = None, **kwargs: Any) -> CliReport: ...
```
No new public methods, no new constructor args on `CliCommands`.

## New internal helper (cli_commands package)

### `workflow_capture.py` (new file)
```python
def capture_workflow_run(
    scan_root: str,
    command: str,
    argument: str,
    report: CliReport,
) -> None:
    """Best-effort: ingest a workflow_run artifact summarizing this call.
    Never raises. Logs a warning on any failure and returns silently."""
```

Called once at the end of each of the 4 `CliCommands` methods, on both
the success and failure return paths (including the nonexistent-path and
scan-failure early returns) — a failed call is itself a real, useful
memory ("guardrails was run against X and failed because Y"), not
something to skip capturing.

**Correction (REVIEWER, post-GATE-5):** the empty/non-string-intent early
returns in `plan()`/`decide()` are the one exception — capture is skipped
entirely for those, not called with `scan_root="."`. These calls never
resolve a real scan target (they fail before any path/repo is known), so
falling back to `"."` would write into whatever directory the caller's
process happens to be running from -- during a test run, that is this
very repo's own `.ortho/ortho.db`, discovered as real, live pollution of
the project's own database during REVIEWER's adversarial pass. See
review.md for the full finding.

`scan_root` is the actual resolved directory that was scanned (or
attempted): `target`/`scan_target` as already computed inside each
method, NOT necessarily the raw `path`/`intent` argument (e.g. `decide()`
with a file-intent scans the file's parent directory — capture must use
that resolved directory, not the file path itself, so `mint_repo_id`
gets a stable directory-shaped input).

## Content Format
```
title = f"{command}: {argument}"  (e.g. "guardrails: repos/click", "plan: add caching")
content = f"success={report.success}\n\n{report.content[:2000]}"
  (2000-char excerpt bound: prevents one artifact from dominating the
  FTS index on a repo with hundreds of violations; 2000 chosen as
  "a few dozen lines of real findings, not the whole dump")
source = "cli"
relevance_scope = "project"
tags = [command]  (e.g. ["guardrails"], ["plan"]) -- enables filtering
  captured runs by which command produced them
type = "workflow_run"
```

## repo_id Resolution
`mint_repo_id(Path(scan_root).resolve())` — same deterministic
sha256-based scheme already used by `index_store.py`/`workflow_cli.py`.
Two calls against the same real directory (even across process restarts)
must produce the same repo_id, and two different directories must
produce different repo_ids (spec acceptance criterion 3).

## Failure Modes That MUST NOT Propagate
| Scenario | Required behavior |
|---|---|
| `scan_root` directory is unwritable (no `.ortho/` can be created) | `capture_workflow_run` catches, logs warning, returns. Original `CliReport` unaffected. |
| `OrthoDatabase.migrate()` raises (corrupt existing `.ortho/ortho.db`) | Same — caught, logged, swallowed. |
| `ArtifactIngestionRequest` fails validation (e.g. empty title after truncation of a bizarre argument) | Same — `ingest_artifact` raises `ValueError` on invalid requests (see ingestion.py); this must be caught too, not just DB-level exceptions. |
| `report.content` contains non-UTF8-safe bytes / extremely long single-line content (no newlines to excerpt cleanly) | `content[:2000]` is a plain string slice — always safe regardless of content shape; no special-casing needed. |
| Two `CliCommands` instances/threads capturing to the same repo concurrently | Out of scope — `ArtifactStore`/`OrthoDatabase` provide no concurrency guarantees beyond SQLite's own WAL mode; not a regression this task introduces (guardrails/decide already had no concurrency story either). |

## Non-Goals (explicit)
- Querying captured workflow runs from the CLI (future task).
- Deduplicating repeated identical runs (every call ingests a new
  artifact; `ArtifactStore`'s own content-hash versioning at the
  `ingest_artifact` layer already handles exact-duplicate-content
  collapsing for free — task-020 does not need to reimplement this).
- Configuring/disabling capture (no on/off flag — always-on, best-effort,
  matches how `_compute_embedding_async` is unconditional today).

## Real-Repo Verification Target
`repos/click` (already the standard fixture for this session) — run all
4 commands, then open `<click_root>/.ortho/ortho.db` directly and query
`artifacts WHERE type='workflow_run'` to confirm 4 real rows, not mocked
storage.
