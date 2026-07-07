# task-011: Scan Persistence + Integration — Plan

**State:** DRAFT (awaiting GATE 1)
**Workflow:** .ases/workflows/feature.md
**Format:** Compact (FRD Part 17)
**Date:** 2026-07-06
**Author:** PLANNER

## Summary

`ortho scan` extracts symbols/imports/calls but persists nothing — `.ortho/ortho.db` stays empty,
so `ortho analyze` and `--impact` (Phase 2 exit criteria) only work against a database no user can
produce. This task closes that gap: scan writes to the database, `ortho context add/search` gets a
CLI, and the full scan → analyze → impact → context chain is proven end-to-end. This is the listed
"Phase 2 completion" work in status.md and the prerequisite for Phase 3 orchestration.

## Atomic Tasks (each = one commit)

| # | Task | Est | Depends |
|---|------|-----|---------|
| 1 | `IndexStore` module (repo-intelligence): persist repositories/files/symbols/call_edges/import_edges rows; symbol ID minting; idempotent per-file rewrite | 90m | — |
| 2 | Wire `Indexer`/`scan_cli.py` to `IndexStore`: `ortho scan` migrates the DB if needed, persists results, stamps `repositories.indexed_at` | 60m | 1 |
| 3 | Migration `002_artifacts_versioning.sql`: reconcile shared `artifacts` schema with context-hub (`version` column, composite PK, FTS5 `content_rowid='rowid'`, sync triggers) | 60m | — |
| 4 | `ortho context add/search`: `context.py` argparse bridge (ArtifactStore + BM25/hybrid) + `context.ts` command, same spawn pattern as analyze | 90m | 3 |
| 5 | End-to-end integration: scan a fixture repo → `analyze --impact` returns non-empty dependents; `context add` → `context search` finds it | 60m | 2,4 |

## Key Data-Model Facts (binding constraints discovered during planning)

- Extractor `Symbol` has NO `id` and NO `end_line` — `IndexStore` mints IDs
  (sha256 of `repo_id:rel_path:qualified_name`, 16 hex, same idiom as context-hub versioning)
  and stores `end_line = lineno` until the extractor learns real spans (documented limitation).
- `symbols.visibility` is NOT NULL CHECK — derive: leading `_` → `private`, else `public`.
- `CallEdge.caller_id/callee_id` from CallGraphBuilder are not DB symbol IDs — map via
  qualified name to minted IDs; edges whose callee doesn't resolve to a repo symbol
  (builtins, external libs) are dropped and counted (evidence line, not an error).
- `ImportEdge` is module-name based (`source_module`/`target_module`) — resolve
  `target_module` to a repo file where possible; else `is_external=1`, `imported_file_id NULL`.
- Schema drift (must fix in Task 3): migration-001 `artifacts` has no `version` column and its
  FTS5 uses `content_rowid='id'` (TEXT — invalid); context-hub `schema.py` expects
  `PRIMARY KEY (id, version)` + rowid-based FTS + triggers. ArtifactStore INSERTs `version`,
  so `context add` fails on a migrated DB today.

## Risks

| Risk | Mitigation |
|------|-----------|
| Schema drift between migration 001 and context-hub schema.py | Task 3 migration is the single source; integration tests run against a *migrated* DB, never a hand-built one |
| Symbol ID collisions (same qualified_name twice in one file) | Deterministic de-dupe: append `:{lineno}` to the hash input on collision |
| Re-scan duplicates rows | Per-file wipe-and-rewrite inside one transaction (delete symbols/edges for file_id, re-insert) |
| Windows file locks on ortho.db | All IndexStore connections scoped + closed (pattern set by model_store fix, 2026-07-06) |
| FTS5 rebuild breaks existing artifact DBs | Migration 002 is idempotent (IF NOT EXISTS / drop+recreate virtual table only when shape is wrong); no user data exists yet in practice |
| Louvain/analyze behavior on freshly persisted graphs differs from unit fixtures | Task 5 end-to-end test asserts non-empty layers/impact on a known fixture repo |

## Acceptance Criteria (binary, repository-independent)

- AC1: After `ortho scan` on a fixture repo, `files`, `symbols`, `call_edges`, `import_edges`
  contain >0 rows each and counts match the scan summary (files, symbols exactly; edges within
  the resolvable subset, unresolved counts reported).
- AC2: Running `ortho scan` twice yields identical row counts (idempotent, no duplicates).
- AC3: `ortho analyze --impact <file-with-known-dependents>` on the scanned fixture returns
  ≥1 direct dependent (the empty-DB era is over).
- AC4: `ortho context add --title T --content C --type note` then `ortho context search "C"`
  returns the artifact, against a migration-002 database.
- AC5: Zero regressions: all existing suites pass (repo-intelligence 85+46xp, context-hub 54,
  arch-intelligence 76, impact-analysis 42, shared/storage 37, apps/cli 16+jest 6, api-server 7,
  tsc --noEmit clean).

## Expected Test Metrics (Fix 4 baseline)

- Unit: 20+ (IndexStore mapping/minting/visibility/resolution rules)
- Integration: 10+ (scan→db, rescan idempotency, migration 002 on fresh + existing db, context add/search)
- Edge: 8+ (empty repo, syntax-error file, duplicate qualified names, unresolvable imports/calls, unicode paths)
- Property-based: ≥1 (hypothesis — minted IDs deterministic + collision-free across generated symbol sets)
- Real-repo: ≥1 (scan fastapi from Repos/, assert ≥500 symbols persisted)
- Coverage: ≥85% on new modules; pass rate 100% (no unmarked failures)

## Out of Scope (do NOT touch)

- Incremental persistence (git-diff-scoped writes) — full rewrite per scan is acceptable now
  (`# ponytail:` marker in code names this ceiling)
- Semantic embeddings (`NullEmbedding` stays the default; sqlite-vec path untouched)
- Detector/analyzer internals (arch_detector, layer/subsystem, impact_analysis) — read-only consumers
- api-server endpoints; file_watcher; duplicate `Symbol` type consolidation (still deferred)

## Architecture Impact

NOT none — new module (`IndexStore`), new CLI surface (`ortho context`), schema migration.
Part 17 fast path does not apply; full ARCHITECT session required at GATE 2.
Expected ADR: ADR-011 (index persistence strategy: minted symbol IDs, per-file
wipe-and-rewrite, unresolved-edge policy).
