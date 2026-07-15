# API Contract Gate — task-020-contexthub-capture

**Verdict:** Contract Valid

## Independent Extraction 1 — spec.md
```
capture_workflow_run(scan_root: str, command: str, argument: str, report: CliReport) -> None
```

## Independent Extraction 2 — architecture-review.md
Confirms same signature and call semantics (best-effort, never raises),
constructed via `OrthoDatabase(resolved_root)` + `ArtifactStore(db,
repo_id=mint_repo_id(resolved_root))`.

## Independent Extraction 3 — Actual Implementation
`workflow_capture.py`: `def capture_workflow_run(scan_root: str, command:
str, argument: str, report: CliReport) -> None` — matches exactly.

## Independent Extraction 4 — Actual Call Patterns
`grep` of every `capture_workflow_run(` call site across `commands.py`
(14 sites, all 4 methods x their success + failure return paths) and
`test_workflow_capture.py` (23 direct calls): 100% use the 4-positional-
arg form `(scan_root, command, argument, report)`, zero keyword-arg or
reordered variants, zero mismatches between implementation and test call
shape.

## Verdict
**Contract Valid.** All four extractions agree exactly on signature and
call pattern; independently confirmed TEST-DESIGNER's blind assumption
(documented in its own file header as unconfirmed at write-time) turned
out to match BUILDER's actual implementation precisely.
