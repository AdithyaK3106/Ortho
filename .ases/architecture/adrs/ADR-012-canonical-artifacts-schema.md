# ADR-012: Canonical Artifacts Schema via Reconciling Migration

**Status:** ACCEPTED (GATE 2, 2026-07-06)
**Date:** 2026-07-06
**Task:** task-011

## Context

Two definitions of the `artifacts` table have drifted:

- **Migration 001** (shared/storage): no `version` column, single-column PK, FTS5 declared with
  `content_rowid='id'` — invalid, since `id` is TEXT and FTS5 external content requires the
  integer rowid — and no sync triggers.
- **context-hub `schema.py`** (shipped, tested, used by ArtifactStore since task-004):
  `PRIMARY KEY (id, version)`, rowid-based FTS5, three sync triggers (ai/au/ad).

ArtifactStore INSERTs a `version` column, so `ortho context add` against a migration-001
database fails immediately. ADR-008 (artifact versioning) already committed to the
composite-key design; migration 001 simply predates it and was never reconciled.

## Decision

- **context-hub's `schema.py` shape is canonical.** Migration
  `002_artifacts_versioning.sql` rebuilds the shared DB's artifacts table to match:
  rename → create canonical → copy (`version = 1`) → recreate FTS5 (`content_rowid='rowid'`)
  → add triggers → drop old table only after row-count parity.
- **Migration 001 stays frozen** (append-only migration history; 002 supersedes its artifacts
  shape). The migration is harmlessly re-runnable (guards in SQL) because
  `OrthoDatabase.migrate()` replays every file on every run.
- Future artifacts-schema changes happen ONLY as new numbered migrations; `schema.py` and the
  migration chain must land in the same task when either changes.

## Alternatives Rejected

- **Edit migration 001 in place:** breaks the append-only migration contract; any existing DB
  would silently diverge from a "fresh" DB.
- **Make ArtifactStore tolerate both shapes:** permanent branching in every query for a
  one-time drift; complexity with no end date.
- **Declare schema.py wrong and drop versioning:** contradicts accepted ADR-008 and shipped,
  tested behavior (54 passing context-hub tests exercise versioning).

## Consequences

- Existing `.ortho/ortho.db` files gain versioned artifacts transparently (all existing rows
  become version 1); copy-fidelity is gated by test (counts + content hashes pre/post).
- FTS index is rebuilt once during migration (repopulated from artifacts content).
- The drift class itself is closed: one canonical shape, one owner (migration chain).
