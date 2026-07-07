# task-011: Scan Persistence + Integration — Test Plan

**Format:** Compact (FRD Part 17)
**Date:** 2026-07-06
**Author:** TEST-DESIGNER (fresh context — zero BUILDER exposure; derived from spec.md,
plan.md, architecture-review.md, ADR-011, ADR-012 only. No implementation file was read.)

## Deliverables

| File | Contents |
|------|----------|
| `packages/repo-intelligence/tests/test_index_store.py` | 58 tests: IndexStore unit/integration/migration/edge/property/real-repo |
| `apps/cli/tests/test_context.py` | 14 tests: context.py bridge via real subprocess (test_analyze.py pattern) |

Import check performed: `storage`, `repo_intelligence.*`, `hypothesis` all resolve in the
suite environment. `repo_intelligence.index_store` intentionally NOT imported/run yet
(BUILDER territory, parallel); both files pass `python -m py_compile` (EXIT: 0).

## Counts vs Expected Metrics (spec.md baseline)

| Category | Expected | Designed | Where |
|----------|----------|----------|-------|
| Unit | 20+ | 30 | TestIndexStoreConstruction(2), TestEnsureRepository(4), TestPersistFileBasics(6), TestSymbolIdMinting(5), TestVisibilityAndKind(5), TestCallEdges(4), TestImportEdges(4) |
| Integration | 10+ | 16 | TestScanFlowIntegration(7), TestImportResolution(4), TestMigration002(5) |
| Edge | 8+ | 10 | TestEdgeCases |
| Property-based | ≥1 (≥10 cases) | 1 (hypothesis, max_examples=10, each example persisted twice into fresh DBs) | TestPropertyBased |
| Real-repo | ≥1 (fastapi ≥500 symbols) | 1 (skipif `Repos/fastapi` absent) | TestRealRepo |
| CLI bridge | — | 14 (TestContextAdd 8, TestContextSearch 6) | apps/cli/tests/test_context.py |
| **Total** | — | **72** | |

All integration tests use `OrthoDatabase(tmp_path).migrate()` — never a hand-built schema
(architecture-review mandate honored; guarded explicitly by
`test_migrated_database_has_all_scan_tables`).

## AC Traceability

| AC | Tests |
|----|-------|
| AC1 scan persists rows, counts match summary | `test_sample_scan_flow_end_to_end`, `test_persist_creates_files_row`, `test_sample_persist_file_counts`, `test_real_repo_fastapi_persists_at_least_500_symbols` |
| AC2 re-scan idempotent, no duplicates | `test_sample_idempotent_repersist`, `test_full_rescan_identical_counts`, `test_minting_stable_across_repersist`, `test_rescan_removes_stale_symbols`, `test_rescan_removes_stale_edges` |
| AC3 `analyze --impact` finds ≥1 dependent | Persisted-data-shape precondition covered: `test_resolve_import_targets_maps_dotted_path` (+`_single_segment_module`) produce exactly the `import_edges.imported_file_id` rows ImpactAnalyzer reads (same shape as `test_analyze._build_indexed_repo`); `test_cross_file_call_resolution` covers call-graph shape. Full CLI e2e (`scan` → `analyze --impact`) is BUILDER Task 5 + VERIFIER Phase C — outside this suite's spec surface. |
| AC4 `context add` → `context search` on a migration-002 DB | `test_sample_context_add_prints_json`, `test_search_returns_added_artifact`, `test_add_persists_row_in_migration_002_db`, entire `TestMigration002` |
| AC5 zero regressions | Regression suite list below (VERIFIER Phase C) |

## Mandated Migration Tests (architecture-review §Migration 002 Design)

- Double-migrate: `test_sample_double_migrate` (fresh, twice, no error),
  `test_double_migrate_preserves_rows` (no duplicate/lost rows, artifacts + scan tables)
- Copy fidelity: `test_migration_copy_fidelity_from_001_shape` — builds a REAL
  migration-001-shaped artifacts table (executescript of 001 only), inserts rows,
  runs `migrate()`; asserts row count, content, content hashes identical, every row
  `version=1`, and copied rows findable via FTS5 MATCH (ADR-012: index repopulated)
- FTS5 triggers post-migration: `test_fts_search_finds_artifact_inserted_after_migration`
  (ai trigger), `test_fts_delete_trigger_syncs` (ad trigger)

## VERIFIER Pilot (GATE 4 / Fix 6) — designated sample tests

Selectable via `-k "test_sample"`; they exercise imports, DB migration, core persist path,
minting, real extractors, and the CLI subprocess protocol:

1. `test_sample_persist_file_counts` (unit — persist_file + PersistResult counts)
2. `test_sample_symbol_id_minting` (unit — sha256 minting formula)
3. `test_sample_scan_flow_end_to_end` (integration — real extractors → store, AC1)
4. `test_sample_idempotent_repersist` (integration — AC2)
5. `test_sample_double_migrate` (migration 002 re-runnability)
6. `test_sample_context_add_prints_json` (CLI bridge subprocess, AC4)

```bash
pytest packages/repo-intelligence/tests/test_index_store.py apps/cli/tests/test_context.py -k "test_sample" -v 2>&1 | tee .ases/evidence/task-011/pilot-test.log
echo "EXIT: $?" >> .ases/evidence/task-011/pilot-test.log
```

## Regression Suites That Must Stay Green (AC5)

- `packages/repo-intelligence/tests/` (85 pass + 46 xpass baseline)
- `packages/context-hub/tests/` (54)
- `packages/arch-intelligence/tests/` (76)
- `packages/impact-analysis/tests/` (42)
- `shared/storage/tests/` (37)
- `apps/cli/tests/` (16 python + this file) and `jest` (6)
- `apps/api-server/tests/` (7)
- `tsc --noEmit` clean

## Known Limitations → Expectations (NOT failures, per spec.md declarations)

| Declared limitation | Reflected as |
|---------------------|--------------|
| `end_line = start_line` (extractor has no end spans) | `test_symbol_row_column_mapping` asserts `end == start == lineno` |
| Dotted-path-only import resolution (no relative/sys.path semantics) | `test_unresolvable_relative_import_stays_external` asserts the relative import is NOT guessed even though the sibling file exists in-repo |
| Full rewrite per scan (no incremental persistence) | Idempotency and stale-row tests assume wipe-and-rewrite (`test_rescan_removes_stale_*`) |

No xfail markers needed: every declared limitation is testable as positive expected behavior.

## Spec Ambiguities Interpreted (→ API CONTRACT GATE)

1. **Collision re-mint assignment:** assumed first-encountered symbol (list order == line
   order) keeps the base hash; each subsequent collider is re-minted with its OWN lineno.
   Asserted exactly in `test_collision_remint_appends_lineno`; triple-collision test only
   asserts distinctness + base-ID presence.
2. **Hash input encoding:** spec formula omits `.encode()` for symbol IDs; assumed UTF-8.
3. **files.id minting rule is unspecified** — tests assert linkage (symbols.file_id →
   files.id) but never a file-ID value.
4. **files.language** assumed `'python'` (NOT NULL column, Python-only pipeline).
5. **rel_path separator convention unspecified** — tests use posix-style strings
   consistently; resolution is expected to map dotted paths onto stored rel_paths.
6. **Cross-file call resolution timing:** "matched ... within the repo" read as resolvable
   when the callee is already persisted; tests only use callee-persisted-first order.
   Whether calls into files persisted LATER must resolve is undefined (imports get an
   explicit second pass; calls do not, per spec/ADR-011).
7. **Unmatched CALLER edges:** spec only defines drop-and-count for unmatched callees.
   Test asserts no row is written for an unmatched caller but does not constrain the
   `calls_dropped_unresolved` counter for that case.
8. **CLI `--repo-root` position:** assumed a top-level flag before the subcommand
   (mirrors analyze.py: `context.py --repo-root <p> add ...`).
9. **Search payload shape:** spec says "one JSON object"; the results-list key is
   unspecified. Tests normalize either `{"results": [...]}` or a bare JSON list; result
   entries are assumed to carry `artifact_id` and `title` (SearchResult field names).
   The `add` payload `{"artifact_id", "version"}` is asserted exactly as spec'd.
10. **`--type note` vs ARTIFACT_TYPES (REAL CONTRACT GAP):** `"note"` is NOT in
    `context_hub.ingestion.ARTIFACT_TYPES` (closest: `dev_note`) and ingestion.py is not
    in the files-to-modify list — yet AC4 mandates `--type note` works. The bridge must
    map or the ingestion vocabulary must change. Tests assert `--type note` exits 0 and
    the artifact is searchable; the stored `type` value is deliberately unasserted.
11. **Version reported by a second identical `add`:** unspecified (ingest short-circuits
    without inserting); only artifact_id equality is asserted.
12. **`--format` default / text shape:** unspecified; JSON assertions always pass
    `--format json`, `--format text` asserted exit-0 + non-empty stdout only.
13. **`is_external` flip on resolution:** inferred from "unresolved stay is_external=1"
    that resolved imports become `is_external=0` with FK set.
14. **Package imports (`pkg` → `pkg/__init__.py`):** resolution unspecified; untested.
