# task-011: Scan Persistence + Integration — Architecture Review

**Format:** Compact (FRD Part 17)
**Date:** 2026-07-06
**Author:** ARCHITECT
**Verdict:** APPROVED

## Module Boundaries

| Module | Responsibility | New/Changed |
|--------|---------------|-------------|
| `repo_intelligence.index_store` | ALL scan-result DB writes; ID minting; import/call resolution | NEW |
| `repo_intelligence.indexer` | Extraction orchestration; hands per-file results to an optional store | CHANGED (additive param) |
| `repo_intelligence.scan_cli` | CLI wiring: migrate → scan → persist → summarize | CHANGED |
| `storage` (shared) | Schema owner; migration 002 canonicalizes artifacts shape | CHANGED (new migration file only) |
| `apps/cli` context bridge | Thin argparse/commander shell over ArtifactStore + search | NEW |

Single-writer rule: `IndexStore` is the only code that writes scan tables
(files/symbols/call_edges/import_edges). Detectors and analyzers stay read-only consumers.
ArtifactStore remains the only artifacts-table writer. No responsibility overlap.

## Dependency Analysis

New edge: `repo-intelligence → shared/storage` (first storage dependency in this package).
Direction: downward, identical to `context-hub → storage` and `arch-intelligence → storage`.
Verified via grep: storage imports nothing from `packages/*` — cycle impossible.

```
apps/cli ─→ repo-intelligence ─→ shared/storage
        └─→ context-hub ────────→ shared/storage
        └─→ arch-intelligence ──→ shared/storage   (unchanged)
```

Script-mode resolution risk: `scan_cli.py` is spawned as a bare script by the TS CLI. `storage`
resolves in the installed env today, but scan_cli MUST include the same sys.path bootstrap idiom
`graph_utils.py` already uses (insert `shared/storage/src`) so the spawn path never depends on
install state. (BUILDER requirement, not optional.)

## API Contracts (validated against real code)

- `IndexStore.__init__(db: OrthoDatabase, repo_id: str, repo_root: Path)` — takes the DB manager,
  not a connection: it owns transaction scope per `persist_file` (scoped, closed connections —
  the 2026-07-06 model_store lock lesson is now a package convention).
- `persist_file(...) -> PersistResult` — deterministic: same inputs → same rows, same counts.
  Delete-then-insert inside ONE transaction; a crash mid-file leaves the previous state (atomic).
- `resolve_import_targets()` — explicit second pass, called once after all files persist.
  Rationale: import targets can reference files scanned later; one-pass resolution would be
  order-dependent, violating the determinism rule every prior task has enforced.
- Spec's minting/visibility/kind mappings were cross-checked against `symbol_extractor.Symbol`
  (`type` within DB CHECK set; `lineno` only — no end spans) and migration 001 constraints. Valid.
- CLI bridge protocol: one JSON object on stdout, exit 0 — same as analyze.py; no new protocol.

## Data Flow & Validation Layer

Validation at the store boundary (IndexStore), not in extractors: extractors stay pure
(parse → dataclasses), IndexStore enforces DB invariants (CHECK sets, NOT NULLs, FK resolution,
collision re-mint). Unresolvable references are *dropped and counted*, never guessed —
consistent with ADR-009's "recognized but excluded" philosophy.

## Migration 002 Design (mandatory ADR-012)

Rename-based rebuild: `artifacts` → `artifacts_old`, create canonical table
(PK `(id, version)`), copy with `version = 1`, recreate FTS5 with `content_rowid='rowid'` +
3 sync triggers, drop `artifacts_old` only after `SELECT COUNT(*)` parity. Idempotency guard:
skip when `pragma_table_info('artifacts')` already shows a `version` column. Runs through the
existing sorted-glob `OrthoDatabase.migrate()` — zero code changes to the migration runner.
NOTE (BUILDER): `executescript` cannot branch; the idempotency guard therefore lives in SQL
(`CREATE TABLE IF NOT EXISTS` + INSERT...SELECT guarded by WHERE NOT EXISTS on pragma) or the
migration is written to be harmlessly re-runnable — TEST-DESIGNER must include a double-migrate test.

## Risks

| Risk | Assessment |
|------|------------|
| FK violations on insert order | IndexStore inserts repo → file → symbols → edges; enforced by method structure |
| Qualified-name call mapping produces false edges (same name, two files) | Accepted at current confidence model (CallEdge.confidence already encodes uncertainty); collision maps to first minted ID by (rel_path, lineno) sort — deterministic. Documented limitation |
| Migration on live DB with artifacts data | rollback-plan.md's copy-fidelity gate; artifacts_old retained until parity proven |
| Performance (fastapi-scale repo) | Batched executemany per file; single transaction per file; fastapi real-repo test is the benchmark gate |

## FRD Compliance

- §14 schema is the persistence target — no schema invention beyond migration 002's
  reconciliation with the already-shipped context-hub shape (drift fix, not new design).
- §~725 symbol-ID rule ("ID is the foreign key everywhere, never raw string names") — minted-ID
  contract implements exactly this.
- Phase 2 exit criteria become end-to-end true (scan → analyze --impact on a real DB).
- Pillar 2 "ortho scan + artifact store integration" checklist items (status.md) close.

## ADRs

- **ADR-011** — Index Persistence Strategy (minted symbol IDs, per-file wipe-and-rewrite,
  drop-and-count unresolved edges) — DRAFTED
- **ADR-012** — Canonical Artifacts Schema via Reconciling Migration (002 supersedes 001's
  artifacts shape; context-hub schema.py is the reference shape) — DRAFTED

## Verdict

**APPROVED** — boundaries clean, dependency direction correct, contracts validated against
actual code, both mandatory ADRs drafted. Proceed to GATE 2 human review.
