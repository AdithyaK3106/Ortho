# task-011: Scan Persistence + Integration — Spec

**Format:** Compact (FRD Part 17)
**Objective:** `ortho scan` persists its index to `.ortho/ortho.db`; `ortho context add/search`
works from the CLI; scan → analyze → impact → context proven end-to-end.

## Files to CREATE

| File | Purpose |
|------|---------|
| `packages/repo-intelligence/src/repo_intelligence/index_store.py` | `IndexStore` — all DB writes for scan results |
| `shared/storage/src/storage/migrations/002_artifacts_versioning.sql` | Reconcile artifacts schema with context-hub (version column, rowid FTS5, triggers) |
| `apps/cli/src/commands/context.py` | argparse bridge: add/search via ArtifactStore + BM25Search/HybridSearch |
| `apps/cli/src/commands/context.ts` | `ortho context add|search` commander command (spawn pattern copied from analyze.ts) |
| `packages/repo-intelligence/tests/test_index_store.py` | Unit + integration tests for persistence |
| `apps/cli/tests/test_context.py` | CLI bridge tests (incl. subprocess entry-point test) |

## Files to MODIFY

| File | Change |
|------|--------|
| `packages/repo-intelligence/src/repo_intelligence/indexer.py` | Collect per-file results and hand them to `IndexStore` when a store is provided (constructor param, default None = current behavior) |
| `packages/repo-intelligence/src/repo_intelligence/scan_cli.py` | Migrate DB if needed, construct `IndexStore`, print persisted counts in summary |
| `apps/cli/src/index.ts` | Register `contextCommand` |
| `packages/context-hub/src/context_hub/schema.py` | No behavior change; docstring note that migration 002 is the canonical shared-DB shape (only if a comment suffices — otherwise do not touch) |

## Files NOT to touch

`arch_detector.py`, `layer_detector.py`, `subsystem_detector.py`, `impact_analysis/*`,
`adr_tracker.py`, `reuse_detector.py`, `file_watcher.py`, `incremental_indexer.py`,
`apps/api-server/*`, `embedding/*`, existing migrations (001 stays frozen).

## Contracts

### IndexStore (new)

```python
class IndexStore:
    def __init__(self, db: OrthoDatabase, repo_id: str, repo_root: Path): ...
    def ensure_repository(self, name: str, primary_language: str = "python") -> None:
        """INSERT OR IGNORE repositories row; update indexed_at on every persist."""
    def persist_file(
        self, rel_path: str, symbols: list[Symbol],
        imports: list[ImportEdge], calls: list[CallEdge],
    ) -> PersistResult:
        """One transaction: delete existing rows for this file, re-insert. Idempotent."""
    def resolve_import_targets(self) -> None:
        """Second pass after all files persisted: map imported_module -> files.id
        (dotted module path relative to repo root); unresolved stay is_external=1."""

@dataclass
class PersistResult:
    symbols_written: int
    imports_written: int
    calls_written: int
    calls_dropped_unresolved: int
```

**Symbol ID minting:** `sha256(f"{repo_id}:{rel_path}:{qualified_name}").hexdigest()[:16]`;
on collision within a file, re-mint with `:{lineno}` appended to the hash input.
**Column mapping:** `kind = symbol.type` (already within CHECK set); `visibility = "private"
if name.startswith("_") else "public"`; `start_line = end_line = symbol.lineno`
(extractor has no end spans — documented limitation); `signature = NULL`; `docstring` as-is.
**Call edges:** caller/callee matched to minted IDs by qualified name within the repo;
edges with unmatched callee are dropped and counted in `calls_dropped_unresolved`.
**repo_id:** `sha256(str(repo_root.resolve()).encode()).hexdigest()[:16]` — stable per root.

### Migration 002 (canonical artifacts shape)

Brings the shared DB to what context-hub's `schema.py` already defines:
`artifacts` gains `version INTEGER NOT NULL DEFAULT 1` with `PRIMARY KEY (id, version)`
(SQLite: rebuild via rename→create→copy→drop), FTS5 virtual table recreated with
`content_rowid='rowid'`, and the three sync triggers (`artifacts_ai/au/ad`) added.
Idempotent: guarded so re-running is a no-op. Runs through the existing
`OrthoDatabase.migrate()` (sorted glob picks it up after 001 — no code change).

### CLI

```
ortho context add --title <t> --content <c> [--type note] [--source manual] [--tags a,b]
ortho context search <query> [--limit 10] [--type <t>] [--format text|json]
```

`context.py` prints one JSON object to stdout, exit 0 on success (same protocol as analyze.py).
Search uses BM25 (HybridSearch degrades to BM25 with NullEmbedding — acceptable; semantic is
out of scope). `add` prints `{"artifact_id": ..., "version": ...}`.

### scan_cli summary extension

Existing summary gains: `Persisted: X symbols, Y imports (Z external), W calls (V dropped unresolved)`.
Exit code semantics unchanged.

## Acceptance Criteria

AC1–AC5 as in plan.md (binary, fixture-based; AC5 = zero regressions across all 7 suites + tsc).

## Expected Test Metrics

Unit 20+ / Integration 10+ / Edge 8+ / property ≥1 (hypothesis ≥10 cases) / real-repo ≥1
(fastapi ≥500 symbols persisted) / coverage ≥85% on new modules / pass rate 100%.

## Known Limitations (declared BEFORE verification)

- `end_line = start_line` for all symbols (extractor emits no end spans). Impact: blast-radius
  line math unaffected (impact analyzer treats 0/None equivalently); future extractor task.
- Import target resolution is dotted-path-only (no sys.path/package-alias semantics);
  unresolved imports are stored as external, never guessed.
- Full rewrite per scan (no git-diff-scoped incremental persistence) — `# ponytail:` ceiling
  documented in code; upgrade path is IncrementalIndexer integration (future task).
