# Ortho v3 — Project Status & Context

**Project:** Ortho v3 — Engineering Decision Engine (vNext COMPLETE)  
**Phase:** vNext COMPLETE — all four roadmap phases built & audited (2026-07-16)  
**Methodology:** ASES v1.2 with FRD Part 17 optimizations  
**Stack:** Python (packages) + TypeScript (CLI/MCP)  
**FRD:** `ortho-v3-frd.md`  
**Last Updated:** 2026-07-21  

---

## 1. Project Overview & Architecture
Ortho is an AI engineering platform that scans a Python repository, builds intelligence (call graphs, imports, architecture patterns), and uses a Selector Engine to route intents to specific agents and skills.

### Core Components
- **Repo Intelligence:** Python AST adapter (tree-sitter), Symbol extraction, Import/Call Graph builder.
- **ContextHub:** SQLite storage, BM25 search (FTS5), Git metadata store.
- **Arch Intelligence:** Architecture Detection (layered, microservices, etc.), Subsystem Clustering, Impact Analysis.
- **Orchestration:** Selector Engine, Workflow Executor, Intent Router, Token Optimizer.
- **Benchmarks:** A modular benchmark framework to validate correctness (precision/recall) against ground-truth datasets.

### Packages (`packages/`)
- `repo-intelligence` — AST parsing, symbol extraction, call/import graph, `RepoGraphQueries`, `SymbolIndex`, `CodeMetricsAdapter`
- `context-hub` — SQLite storage, BM25 (FTS5), semantic search, `ArtifactStore`, workflow_run capture
- `arch-intelligence` — Architecture detection (5 styles), subsystem clustering, `ArchModelAdapter`
- `arch-guardrails` — Layer-boundary enforcement, violation detection, `ArchitectureEnforcer`
- `change-planner` — Blast-radius / impact analysis, `ChangePredictor`
- `decision-engine` — Multi-source decision synthesis, `DecisionEngine`
- `feature-planner` — Feature implementation paths
- `refactoring-advisor` — Bloat/coupling/cycle findings
- `impact-analysis` — Impact scoring utilities
- `orchestration` — ASES workflow executor, intent router, selector engine, agent/skill registry
- `token-optimizer` — 9-component context optimization pipeline
- `cli-commands` — `CliCommands` Python bridge; `DependencyGraphAdapter`, all copilot commands
- `dashboard-generator` — Reporting utilities

### Apps (`apps/`)
- `cli` — TypeScript CLI entry point (`ortho` binary), `pybridge.ts`, `copilot.ts`
- `mcp-server` — 10-tool MCP server (stdio, all verified end-to-end)
- `api-server` — REST API (FastAPI)

### Architecture Decisions (ADRs)
- **ADR-004:** Storage Strategy — SQLite local-first.
- **ADR-005:** Language Adapter Plugin Model.
- **ADR-013:** Semantic-router adoption for Intent classification.
- **ADR-014:** Pure Python Selector Engine (no LLM in selector).
- **ADR-015:** Layer Boundaries & Import Rules — enforces one-way acyclic dependencies (see `docs/architecture/adr-015-layer-boundaries.md`).
- **ADR-016:** Engineering Copilot Layer — classifies `change-planner`, `feature-planner`, `refactoring-advisor`, `arch-guardrails`, `decision-engine` between Apps and Intelligence layers.

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

## 3a. Known Limitations & Documented Gaps

### Task-015 (Engineering Benchmark Suite) — 90% Complete
- **Status:** COMMITTED with documented gap
- **Coverage:** 45/50 repositories benchmarked (90% vs. 100% target)
- **Mitigation:** Phase 5 includes completion of missing 5 repos
- **Reference:** `docs/archive/TASK_015_ACCEPTANCE_GAP.md`

### layer_boundaries
- Redesigned and unit-tested on synthetic fixtures only; never observed firing on a real repo.

### cross-repo
- O(n²) cliff at >2000 pooled symbols — guarded with a fast-fail and actionable error message.

### arch-intelligence
- 106 pre-existing mypy --strict errors (legacy, documented). Architecture-detection accuracy regressed 83.3%→75% on vendored `repos/sqlalchemy` (Python 3.14 syntax the parser can't handle). Not fixed; tracked.

### feature-planner
- Intent-classification miss on non-web-service repos (documented gap).

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
- [ ] Phase 5: Complete missing 5 benchmark repos (Task-015 gap)

**See:** `docs/archive/CLEANUP_PLAN.md`, `docs/architecture/adr-015-layer-boundaries.md`

---

## 5. Current Status & Active Work

**✅ ORIGINAL PHASES 1-6 COMPLETE & VERIFIED** (foundation, reasoning,
execution, architecture intelligence, engineering intelligence — see git
history and `docs/archive/` for per-phase detail).

**✅ vNEXT ROADMAP: ALL FOUR PHASES BUILT & AUDITED (2026-07-16)**
Ortho is now the Engineering Decision Engine described in
`PILOT_READINESS.md`, not just a scanner:
- **Evidence Engine** — every finding carries real, checkable evidence
- **Unified `ortho review`** + **Test Intelligence** (recommended tests, coverage gaps)
- **Accept/reject feedback loop** — "rejected before, here's why" citations (the moat; `ortho feedback`)
- **Repository Q&A** (`ortho ask`), **Cross-Repo Intelligence** (`ortho cross-repo`), **Workflow Orchestration** (`ortho orchestrate`)
- **Memory search** (`ortho memory search <query>`) — BM25 over `.ortho/ortho.db` workflow_run artifacts
- **Severity/confidence filtering** — `--severity error|warning`, `--confidence 0.0-1.0`
- **Structured JSON output** — `CliReport.violations` / `CliReport.recommendations` for MCP consumers
- 10 MCP tools — all verified end-to-end via real stdio round-trip

**CLI Commands (complete list):**
- `ortho init` / `ortho scan` / `ortho index --since` — bootstrap & indexing
- `ortho context add/search/list/stats` — ContextHub operations
- `ortho analyze [--impact|--debt|--deps]` — architecture reports
- `ortho guardrails [path] [--severity error|warning]` — layer-boundary violations
- `ortho decide <intent> [--scan-path] [--confidence N]` — decision support
- `ortho plan <intent> [--scan-path]` — feature implementation paths
- `ortho refactor [path]` — bloat/coupling/cycle findings
- `ortho ask <question>` — repository Q&A
- `ortho cross-repo` — cross-repo intelligence
- `ortho orchestrate` — workflow orchestration (never auto-approves)
- `ortho feedback` — accept/reject feedback loop
- `ortho memory search <query>` — search past workflow artifacts
- `ortho run` / `ortho status` / `ortho approve` / `ortho reject` / `ortho history` — ASES workflow management
- `ortho debug run/context` — debugging

**Audit Summary (2026-07-16):**
- **Total Tests:** 1375 passed, 3 failed (pre-existing architecture-classifier benchmark gaps only), zero new regressions
- **mypy --strict:** clean on all active packages (arch-intelligence 106 legacy errors documented)
- **Production Status:** feature-complete and audited — **blocked on the five-pilot study, not on engineering**
- **Next action:** pilot recruitment per `PILOT_READINESS.md` §14

**Historical milestones (in order):**
- Tasks 020–024 (2026-07-15): ContextHub capture, CLI copilot exposure, structured JSON, filtering, memory search
- Task-017 (2026-07-14): Real CLI wiring — `guardrails`/`decide` now call real engines (was 100% stubs)
- Tasks 018–019 (2026-07-15): layer_boundaries false-positive reduction (92%), plan/refactor real engines
- Production Readiness Audit (2026-07-15): fixed critical install bug (8 of 13 packages silently not installed), broken relative imports, unbounded-scan regression, mypy violations
- False-Positive Audit (2026-07-16): 91%→0% verified false-positive rate on 9-repo hand-audit
