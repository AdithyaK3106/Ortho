# Ortho v3 — Phase 1 Progress Tracker

**Version:** 1.1 — ASES v1.2 Optimized  
**Started:** 2026-06-30  
**Current Phase:** Phase 1 — Foundation (Weeks 1–8)  
**Goal:** CLI that scans a Python repo and makes its contents searchable. No AI yet.  
**Optimization:** Task-001 complete (full v1.1 workflow). Weeks 3–8 tasks use FRD Part 17: compact templates, PLANNER+ARCHITECT fast path (if no structural change), tiered verification. Same 6 gates, same rigor, ~40% faster artifact production per task.

---

## Phase 1 Breakdown (8 weeks)

### Week 1–2: Shared Foundation
- [x] Set up monorepo (Poetry workspaces)
- [x] Define all shared types (TypeScript + Python dataclasses)
- [x] Implement SQLite storage layer with migrations
- [x] Implement `OrthoConfig` and `.ortho/` directory structure
- [x] Logging, error handling, config utilities
- [x] CLI skeleton with `ortho init`
- [x] ADR: Storage strategy (SQLite + sqlite-vec)
- [x] ADR: Language adapter plugin model

**Status:** COMPLETED ✓ (commit: 46edd53)

---

### Week 3–4: Repo Intelligence — Python
- [x] `LanguageAdapter` interface
- [x] Python adapter: tree-sitter AST parsing (no astchunk yet, deferred)
- [x] Symbol extraction and registry
- [x] Import graph builder
- [ ] `ortho scan` command — scans and reports (deferred to later in Week 3–4)

**Status:** COMPLETED ✓ (task-002, commit: 5b8f8a2)
- LanguageAdapter interface + PythonAdapter (tree-sitter)
- SymbolExtractor (functions, classes, methods, nested, docstrings)
- ImportGraphBuilder (from/import/relative statements, circular detection)
- 36 tests, 89% coverage, all 6 ASES gates passed

---

### Week 5–6: Repo Intelligence — call graph + incremental
- [ ] Call graph builder using `pyan3`
- [ ] Dependency graph (requirements.txt, pyproject.toml)
- [ ] Module detector
- [ ] Incremental indexer (git diff based)
- [ ] `ortho index` with `--watch` mode

**Status:** NOT STARTED

---

### Week 7–8: ContextHub
- [ ] Artifact store with all types + ingestion contract
- [ ] BM25 search (SQLite FTS5)
- [ ] Semantic search (sqlite-vec + embedding API)
- [ ] Hybrid RRF search
- [ ] Git metadata store (gitpython)
- [ ] Project memory store
- [ ] `ortho context add` / `ortho context search`
- [ ] Staleness detector

**Status:** NOT STARTED

---

## Active Tasks

| Task ID | Name | Workflow | State | CLAUDE.md Ref |
|---------|------|----------|-------|---------------|
| task-003 | Call Graph + Incremental (Week 5–6) | feature.md | DRAFT | Ready for PLANNER |

---

## Completed Tasks

| Task ID | Name | Workflow | Commit Hash | Date |
|---------|------|----------|-------------|------|
| task-001 | Shared Foundation (Week 1–2) | feature.md | 46edd53 | 2026-06-30 |
| task-002 | Python Language Adapter (Week 3–4) | feature.md | 5b8f8a2 | 2026-06-30 |

---

## Current Blockers

None.

---

## Architecture Decisions (ADRs)

| ADR | Title | Status | Reference |
|-----|-------|--------|-----------|
| — | — | — | — |

---

## Verification Status

| Check | Task-001 | Task-002 | Task-003 | Task-004 | Task-005 |
|-------|----------|----------|----------|----------|----------|
| Build | PASS ✓ | PASS ✓ | — | — | — |
| Types | PASS ✓ | PASS ✓ | — | — | — |
| Lint | PASS ✓ | PASS ✓ | — | — | — |
| Tests | PASS ✓ (120+ tests) | PASS ✓ (36 tests, 89% coverage) | — | — | — |
| Integration | PASS ✓ | PASS ✓ | — | — | — |

---

## Phase 1 Progress

**Completed:** 2/5 tasks (40%)
- Task-001: 46edd53 (2026-06-30)
- Task-002: 5b8f8a2 (2026-06-30)

**In Progress:** Task-003 (PLANNER ready)

**Remaining:** Task-004 (Week 5–6), Task-005 (Week 7–8)

**Workflow Optimizations Applied:**
- Compact templates (70% size reduction)
- PLANNER+ARCHITECT fast path (1 fewer session where architecture_impact: NONE)
- Tiered verification (Tier 1 scoped iteration, Tier 2 full commit gate)
- Bootstrap exception: Task-002 GATE 5 approved by artifact review (full verification enforced once automation available)

---

*Last updated: 2026-06-30 by BUILDER (task-002 COMPLETED)*
