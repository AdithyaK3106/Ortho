# Ortho v3 — Phase 1 Progress Tracker

**Version:** 1.0  
**Started:** 2026-06-30  
**Current Phase:** Phase 1 — Foundation (Weeks 1–8)  
**Goal:** CLI that scans a Python repo and makes its contents searchable. No AI yet.

---

## Phase 1 Breakdown (8 weeks)

### Week 1–2: Shared Foundation
- [ ] Set up monorepo (Poetry workspaces)
- [ ] Define all shared types (TypeScript + Python dataclasses)
- [ ] Implement SQLite storage layer with migrations
- [ ] Implement `OrthoConfig` and `.ortho/` directory structure
- [ ] Logging, error handling, config utilities
- [ ] CLI skeleton with `ortho init`
- [ ] ADR: Storage strategy (SQLite + sqlite-vec)
- [ ] ADR: Language adapter plugin model

**Status:** ARCHITECT-COMPLETE → READY-FOR-HUMAN-APPROVAL-GATE-2

---

### Week 3–4: Repo Intelligence — Python
- [ ] `LanguageAdapter` interface
- [ ] Python adapter: tree-sitter AST + `astchunk` integration
- [ ] Symbol extraction and registry
- [ ] Import graph builder
- [ ] `ortho scan` command — scans and reports

**Status:** NOT STARTED

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
| task-001 | Shared Foundation (Week 1–2) | feature.md | ARCH-REVIEW-COMPLETE | Awaiting GATE 2 approval |

---

## Completed Tasks

| Task ID | Name | Workflow | Commit Hash | Date |
|---------|------|----------|-------------|------|
| — | None yet | — | — | — |

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

**Build:** Not started  
**Types:** Not started  
**Lint:** Not started  
**Tests:** Not started  
**Integration:** Not started

---

*Last updated: 2026-06-30 by ARCHITECT (architecture review complete, awaiting GATE 2 approval)*
