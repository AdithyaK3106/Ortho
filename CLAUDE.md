# Ortho v3 — Project Status & Context

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 3 (Execution) / Phase 4 (Intent & Planning)  
**Methodology:** ASES v1.2 with FRD Part 17 optimizations  
**Stack:** Python (packages) + TypeScript (CLI)  
**FRD:** `ortho-v3-frd.md`  

---

## 1. Project Overview & Architecture
Ortho is an AI engineering platform that scans a Python repository, builds intelligence (call graphs, imports, architecture patterns), and uses a Selector Engine to route intents to specific agents and skills.

### Core Components
- **Repo Intelligence:** Python AST adapter (tree-sitter), Symbol extraction, Import/Call Graph builder.
- **ContextHub:** SQLite storage, BM25 search (FTS5), Git metadata store.
- **Arch Intelligence:** Architecture Detection (layered, microservices, etc.), Subsystem Clustering, Impact Analysis.
- **Orchestration:** Selector Engine, Workflow Executor, Intent Router, Token Optimizer.
- **Benchmarks:** A modular benchmark framework to validate correctness (precision/recall) against ground-truth datasets.

### Architecture Decisions (ADRs)
- **ADR-004:** Storage Strategy — SQLite local-first.
- **ADR-005:** Language Adapter Plugin Model.
- **ADR-013:** Semantic-router adoption for Intent classification.
- **ADR-014:** Pure Python Selector Engine (no LLM in selector).
- **ADR-015:** Layer Boundaries & Import Rules — enforces one-way acyclic dependencies (see `docs/architecture/adr-015-layer-boundaries.md`).

---

## 2. Key Decisions & Development Rules

1. **Methodology:** Strict ASES workflow. Every feature requires PLANNER → ARCHITECT → BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER.
2. **Local-first:** No cloud, no auth, SQLite only.
3. **Type safety:** Strict TypeScript (no `any`), `mypy --strict` for Python.
4. **Reproducibility:** All metrics and benchmarks must be backed by reproducible code and hand-authored ground truth (No simulated metrics).

---

## 3. Test Execution Policy (Mandatory)
All tests MUST be run and verified. Simulated logs are strictly prohibited.
- **VERIFIER Mode A:** pytest MUST be executed. Example: `pytest packages/[pkg]/tests/ -v --tb=short`
- **GATE 5 Enforcement:** A human must spot-check the actual test log file to confirm EXIT codes and output.
- **Expected Results:** Test metrics and expectations must be documented in `spec.md` before implementation. 

---

## 4. Codebase Health & Cleanup (2026-07-12)

### Completed Cleanup
- ✅ Deleted orphaned `apps/api_server/` directory (was duplicate of `api-server`)
- ✅ Deleted empty src-level `__init__.py` files (Python 3.3+ supports implicit namespaces)
- ✅ Updated `.gitignore` to exclude `.mypy_cache/`, `.hypothesis/`, `.ruff_cache/`
- ✅ Consolidated API server: merged orchestration router into main app
- ✅ Added ADR-015 for layer boundaries and import rules
- ✅ All packages have `__all__` exports (public API contracts)

### Remaining Tasks (Deferred)
- [ ] Phase 4: Reorganize into `core/`, `intelligence/`, `storage/` top-level directories (non-breaking, optional)
- [ ] Phase 5: Consolidate test fixtures into `benchmarks/fixtures/` (low priority)

**See:** `CLEANUP_PLAN.md`, `docs/architecture/adr-015-layer-boundaries.md`

---

## 5. Current Status & Active Work
Phase 1 & 2 are complete (Foundation & Reasoning).
Phase 3 (Execution) is mostly complete (Intent Routing, Selector Engine, Token Optimizer).

**Recent Completions:**
- **task-012:** Intent Routing & Registries
- **task-013:** Selector Engine & Execution
- **task-014:** Token Optimizer
- **task-016:** Engineering Benchmark Suite

**Next Steps:**
- **Phase 4 (Intent & Planning):** Integrating the Token Optimizer with full workflow execution and LLM fallback routing.
