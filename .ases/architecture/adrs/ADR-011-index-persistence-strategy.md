# ADR-011: Index Persistence Strategy

**Status:** ACCEPTED (GATE 2, 2026-07-06)
**Date:** 2026-07-06
**Task:** task-011

## Context

`ortho scan` extracts symbols/imports/calls but persists nothing, leaving `.ortho/ortho.db`
empty and making `ortho analyze` / `--impact` unusable end-to-end. Extractor dataclasses carry
no database IDs (`Symbol` has no `id`, `ImportEdge` is module-name based), while the FRD (§14,
symbol-ID rule) requires stable IDs as the universal foreign key.

## Decision

1. **Minted, deterministic symbol IDs:** `sha256(f"{repo_id}:{rel_path}:{qualified_name}")[:16]`,
   with `:{lineno}` appended to the hash input on intra-file collision. Same repo + path +
   symbol always yields the same ID across scans — stable FKs without extractor changes.
2. **Per-file wipe-and-rewrite in one transaction:** on persist, delete all rows keyed to the
   file_id, re-insert current results. Idempotent re-scans, atomic per file, no diffing logic.
   `# ponytail:` ceiling — full rewrite per scan; upgrade path is IncrementalIndexer-scoped
   persistence when scan time on large repos matters.
3. **Drop-and-count unresolved references:** call edges whose callee isn't a repo symbol and
   imports that don't resolve to a repo file are never guessed — calls are dropped (counted in
   `PersistResult.calls_dropped_unresolved`), imports stored with `is_external=1`.
4. **Single writer:** `IndexStore` is the only writer of scan tables. Analyzers stay read-only.
5. **Two-pass import resolution:** all files persist first, then `resolve_import_targets()` maps
   `imported_module` → `files.id` — resolution is order-independent, hence deterministic.

## Alternatives Rejected

- **AUTOINCREMENT integer symbol IDs:** unstable across re-scans; breaks the FRD's
  ID-as-universal-FK rule and any artifact that stored a symbol reference.
- **UPSERT/diff-based persistence:** requires change detection per row; wipe-and-rewrite is
  strictly simpler and idempotent by construction. Revisit only with incremental persistence.
- **Extending extractors to emit IDs:** couples pure parsers to storage concerns and touches
  three stable, fully-tested modules; the store boundary is the right home for DB invariants.

## Consequences

- Re-scan cost is O(repo) always (accepted; measured by the fastapi real-repo test).
- `end_line = start_line` until extractors emit spans (declared limitation, task-011 spec).
- Same-name symbols in different files can blur call-edge mapping; deterministic
  first-match by (rel_path, lineno) sort, uncertainty already encoded in CallEdge.confidence.
