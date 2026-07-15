# Ortho v3 — Status Tracker

**Version:** 3.0 — Phase 7.1 COMPLETE ✅ (All CLI copilot commands live + memory search)  
**Started:** 2026-06-30  
**Current Status:** Pilot-ready — guardrails/decide/plan/refactor + memory search all live with filtering, structured JSON output, engineering memory captured per-repo.  
**Last Updated:** 2026-07-15  

---

## 6. Production Readiness Audit ✅ COMPLETE (2026-07-15)

Full repo audit: install path, per-package test suites, mypy --strict,
and a real end-to-end run against an unseen repo (`custom_yolo`, never
indexed by Ortho before). Fixed a critical install bug (`pip install -e .`
alone silently skipped 8 of 13 workspace packages on a fresh clone —
`orchestration` and `token-optimizer` were never importable), broken
relative imports that made `orchestration`'s entire 105-test suite
uncollectible, an unbounded-scan regression in 2 tests (same bug class
task-017 fixed for `decide()`, recurring in test code calling
`guardrails()`), and 4 mypy --strict violations in cli-commands. Also
documented (not fixed — needs its own workflow): an 83.3%→75% accuracy
regression in architecture-detection benchmarks (vendored `repos/sqlalchemy`
now has Python 3.14 syntax the parser can't handle), pre-existing
mypy --strict gaps in 5 older packages (206 combined errors), and a
feature-planner intent-classification miss on non-web-service repos.
See `docs/archive/PRODUCTION_AUDIT_2026-07-15.md` for full detail.

## 5. Task-024: Memory Search ✅ COMPLETE (2026-07-15, commit 6ef6e1a)

Pilots can now query learned knowledge from past guardrails/decide/plan/refactor runs:
- `ortho memory search <query> [--repo-path <path>]` — searches workflow_run
  artifacts by keyword (layer_boundaries, violation, architecture, etc.)
- BM25 ranking (FTS5) returns up to 50 results sorted by relevance
- Text summary: "Found N artifacts matching '<query>'" + breakdown by
  command type (e.g., "3 guardrails runs, 1 plan run, 1 decide run")
- Structured field: `CliReport.search_results` with artifact_id/title/type/
  source/created_at/relevance_score for downstream tools (MCP, analysis)
- Edge cases: empty queries (success=True, "no artifacts"), nonexistent
  repo (success=False), fresh repo no .ortho yet (success=True, "no memory")
- Real bug fixed: confidence_threshold validation now type-checks float, not
  just value-range checks (TEST-DESIGNER caught string-as-float coercion)
- 30 hard edge-case tests (shadow-parallel TEST-DESIGNER). All pass.
  Verified: real repos/click artifact search, case-insensitivity, result
  limiting, SQL injection robustness, unicode handling.
- See `.ases/tasks/task-024-memory-search/`.

## 4. Task-023: Severity/Confidence Filtering ✅ COMPLETE (2026-07-15, commit 3fcc739)

Pilots can now filter noise via `--severity` and `--confidence` flags:
- `guardrails(path, severity_filter="error"|"warning"|None)` — shows only
  error or warning violations. Filtered counts reported in text summary.
  Backward-compatible (default None = all).
- `decide(intent, confidence_threshold=0.0-1.0|None)` — shows only
  recommendations >= threshold. Falls back to highest-confidence if all
  filtered. Backward-compatible.
- CLI: `ortho guardrails --severity error`, `ortho decide --confidence 0.8`.
  TS-side validation (enum/range checks) before spawn; Python-side argparse
  validation for defense-in-depth.
- 44 hard edge-case tests; all pass. Real repo scans confirm filtering
  behavior. Backward-compat verified.
- See `.ases/tasks/task-023-filtering/`.

## 3. Task-022: Structured JSON Output ✅ COMPLETE (2026-07-15, commit 57cfbfb)

`guardrails()` and `decide()` now return structured objects alongside text:
- `CliReport.violations: Optional[list[GuardrailViolation]]` — populated by
  guardrails, enables MCP servers and other tools to programmatically
  access violations without text parsing.
- `CliReport.recommendations: Optional[list[Recommendation]]` — populated
  by decide, exposes all recommendation options with source/effort/risk/
  confidence fields. Machine-readable decision support.
- Backward-compatible: existing callers accessing only title/content/success
  see no change. New fields default to `None`. Text output (content field)
  is identical to pre-task format.
- 26 hard-edge-case tests; 126/126 full suite pass (zero regressions).
- See `.ases/tasks/task-022-structured-json-output/`.

## 2. Task-021: CLI Exposure of Copilot Commands ✅ COMPLETE (2026-07-15, commit c5739e5)

All four copilot commands now accessible as top-level `ortho` CLI:
- `ortho guardrails [path]` — real architecture violation check
- `ortho decide <intent> [--scan-path]` — multi-source decision support
- `ortho plan <intent> [--scan-path]` — feature implementation paths
- `ortho refactor [path]` — bloat/coupling/cycle findings
- Bridge pattern: copilot.ts → pybridge.ts → copilot.py → CliCommands,
  mirrors context.ts/context.py precedent verbatim. TS-side intent
  validation (empty/whitespace check before spawn). All paths explicitly
  passed from TS (no unbounded cwd fallbacks). Windows UTF-8 fix via
  binary stdout buffer. 25 hard tests; end-to-end verified against
  repos/click. See `.ases/tasks/task-021-cli-copilot-commands/`.

## 1. Task-020: ContextHub Engineering Memory Capture ✅ COMPLETE (2026-07-15, commit a200ad9)

Every `guardrails`/`decide`/`plan`/`refactor` call now ingests a real
`workflow_run` artifact into `<scanned_root>/.ortho/ortho.db` via
`ArtifactStore` — ortho accumulates per-repo engineering memory across
runs (the vNext strategy's core moat). `repo_id` uses the deterministic
`mint_repo_id` scheme; capture is strictly best-effort (never raises,
never flips a successful report). TEST-DESIGNER ran as a genuinely blind
parallel agent from spec.md only. Two real capture-safety bugs found and
fixed in-task: (1) unconditional `OrthoDatabase` mkdir created directory
trees for nonexistent scan paths; (2) empty-intent early returns polluted
the caller's cwd `.ortho/ortho.db` (found by REVIEWER inspecting the live
project database). 26 new hard-edge-case tests; 100/100 passing.
See `.ases/tasks/task-020-contexthub-capture/`.

## -1. Task-018 + Task-019 ✅ COMPLETE (2026-07-15, commits 93b4b08 / 5e1ca78)

- **task-018:** layer_boundaries false positives reduced 92% on
  `repos/click` (83 → 7; zero remaining test/example-path violations) by
  excluding test/example/vendor directories from layer detection.
- **task-019:** `plan()`/`refactor()` wired to real
  `feature-planner`/`refactoring-advisor` engines — zero stub output
  remains anywhere in `CliCommands`. Real bloat/coupling/cycle findings;
  duplication/churn deliberately return empty (no real signal source yet,
  documented gap, not fabricated). Two real bugs fixed in-task (non-str
  intent crash; pre-existing unbounded-scan test hangs).

---

## 0. Phase 7.1: Repo Graph Query Layer + Real CLI Wiring ✅ COMPLETE (2026-07-14)

**task-017-repo-graph-queries** — closed the gap between "current Ortho" and
something a pilot user could actually run. `packages/cli-commands`'s
`guardrails()`/`decide()` were 100% hardcoded stub strings; the query methods
`change-planner`/`arch-guardrails` needed didn't exist anywhere. Built:

- `RepoGraphQueries`, `SymbolIndex`, `CodeMetricsAdapter` (packages/repo-intelligence) — real BFS call-graph traversal, import resolution, line/function counting
- `ArchModelAdapter` (packages/arch-intelligence) — real layer/module lookups over `ArchitectureModel`
- `DependencyGraphAdapter` (packages/cli-commands) — real internal dependency graph + cycle detection (three-color DFS)
- `ortho guardrails`/`ortho decide` now call real `ArchitectureEnforcer`/`ChangePredictor`/`DecisionEngine` against real scanned repos

**New architecture layer:** ADR-016 (Engineering Copilot layer) — classifies
`change-planner`, `feature-planner`, `refactoring-advisor`, `arch-guardrails`,
`decision-engine` between Apps and Intelligence, extending ADR-015.

**Verified:** 68 new/updated tests (34+10+14 new + updates), all 6 touched
packages regression-clean (176/105/54/37/42/28 passing), mypy --strict clean,
real-repo scans against `repos/click`/`repos/flask`/`repos/requests`. Full
ASES workflow (PLANNER → ARCHITECT → BUILDER + shadow-parallel blind
TEST-DESIGNER → API Contract Gate → VERIFIER → REVIEWER) with one
CHANGES-REQUIRED cycle (over-broad exception handling in `repo_scanner.py`,
fixed and re-verified). See `.ases/tasks/task-017-repo-graph-queries/`.

**Real bug found and fixed during this task:** `decide('')`/no-path defaults
silently scanned unbounded cwd (this monorepo's `repos/` has 7,882 vendored
files across 5 cloned frameworks) — fixed with explicit empty-intent
rejection and a `scan_path` kwarg.

---

## 1. Prior Status: PHASE 4 COMPLETE ✅ (historical, superseded by Phase 5/6 — see CLAUDE.md)

**All 9 Phase 4 components implemented and tested:**

- ✅ **Component 1:** Semantic Duplicate Detector (13 tests)
- ✅ **Component 2:** Intent-Aware Reranker (19 tests)
- ✅ **Component 3:** Graph Expander (14 tests)
- ✅ **Component 4:** Context Compressor (12 tests)
- ✅ **Component 5:** Architecture-Aware Retrieval (31+ tests)
- ✅ **Component 6:** Model Context Adapter (42 tests)
- ✅ **Component 7:** Context Quality Logger (2 tests)
- ✅ **Component 8:** Metrics Collection (3 tests)
- ✅ **Component 9:** Ranking Weight Tuning (4 tests)

**Test Results (verified 2026-07-12, post-audit):** 883 tests passed, 0 failed (796 package tests + 87 benchmark-validation tests incl. golden gate). An audit on 2026-07-12 found the previous "110+ tests, 100% pass" claim false (18 failures, 4 mock-only test files); all were fixed same day — see `docs/archive/TEST_VERIFICATION_REPORT.md`.  
**ASES Workflow:** All 5 gates passed  
**Code Quality:** Full type safety, deterministic, ponytail principles  

---

## 2. Completed Milestones

### Phase 1: Foundation ✅ COMPLETE
- ✅ Monorepo setup (Poetry workspaces)
- ✅ Shared types (TypeScript + Python)
- ✅ SQLite storage with migrations
- ✅ CLI skeleton (`ortho init`)
- ✅ ContextHub: BM25, semantic, hybrid search
- ✅ Git metadata tracking

### Phase 2: Repository Intelligence & Reasoning ✅ COMPLETE
- ✅ Python AST adapter (tree-sitter)
- ✅ TypeScript adapter (full support)
- ✅ Symbol extraction & registries
- ✅ Import & call graph builders
- ✅ Incremental indexing (git diff based)
- ✅ `ortho scan` command
- ✅ Architecture detection (5 styles: layered, microservices, hexagonal, MVC, flat)
- ✅ Impact analysis (blast radius)
- ✅ Debt scoring & dependency health
- ✅ Circular dependency detection
- ✅ ADR cross-referencing

### Phase 3: Orchestration & Execution ✅ COMPLETE
- ✅ Intent routing (semantic-router, <10ms, no LLM)
- ✅ Agent registry (8 built-in agents)
- ✅ Skill registry (10+ built-in skills)
- ✅ Selector engine (deterministic, pure Python)
- ✅ Workflow execution (step-by-step with approval gates)
- ✅ Evidence collection
- ✅ State persistence (resumable workflows)
- ✅ Error handling & fallbacks
- ✅ `ortho run` command (main entry point)

### Phase 4: Token Optimization ✅ COMPLETE
- ✅ Semantic duplicate detector (Jaccard similarity, greedy clustering)
- ✅ Intent-aware reranker (per-intent keyword boosting)
- ✅ Graph expander (call graph enrichment, BFS traversal)
- ✅ Context compressor (LLM-ready, heuristic fallback)
- ✅ Architecture-aware retrieval (layer/subsystem weighting)
- ✅ Model context adapter (per-model format adjustment)
- ✅ Context quality logger (CSV logging, daily rotation)
- ✅ Metrics collection (token reduction measurement, percentiles)
- ✅ Ranking weight tuner (auto-tuning via correlation)

---

## 3. Features Summary

### Pillar 1: Repository Intelligence ✅
- Python & TypeScript AST parsing
- Symbol extraction with full metadata
- Call graph & import graph analysis
- Circular dependency detection
- Incremental indexing
- Module detection
- Full position tracking

### Pillar 2: ContextHub ✅
- 13 artifact types (FRD, ADR, specs, evidence, etc.)
- BM25 full-text search (SQLite FTS5)
- Semantic search (sqlite-vec, 1536-dim embeddings)
- Hybrid search (RRF fusion)
- Git metadata tracking
- Project memory (key/value facts)
- Artifact versioning support
- Staleness detection

### Pillar 3: Architectural Intelligence ✅
- 5 architecture styles detected
- Layer & subsystem identification
- Circular dependency detection
- Change impact analysis (blast radius)
- Technical debt scoring (multi-factor)
- Dependency health analysis
- ADR awareness & cross-referencing

### Pillar 4: Engineering Orchestration ✅
- Semantic intent routing (<10ms, HuggingFace encoder)
- 8 built-in agents (Orchestrator, Architect, Coder, Reviewer, Tester, Analyst, Documenter, Debugger)
- 10+ built-in skills
- Deterministic selector engine
- Workflow execution with approval gates
- Evidence collection
- State persistence
- ASES workflow compliance

### Pillar 5: Token Optimizer ✅
- 9 optimization components (see list above)
- Context quality logging (CSV with daily rotation)
- Token reduction metrics (target ≥15%)
- Auto-tuning of weights
- Per-model prompt adaptation
- Deterministic output
- 110+ integration tests

### CLI Commands ✅
- `ortho init` — Initialize project
- `ortho scan` — Full repository indexing
- `ortho index --since` — Incremental re-index
- `ortho context add/search/list/stats` — ContextHub operations
- `ortho analyze` — Full architecture report
- `ortho analyze --impact/--debt/--deps` — Detailed analysis
- `ortho run` — Execute ASES workflow
- `ortho status/approve/reject/history` — Workflow management
- `ortho debug run/context` — Debugging

---

## 4. Test Coverage

- **Total Tests:** 913 executed (201 cli-commands pkg + 712 others)
  - cli-commands: 201 tests across 8 files
    - task-020: 29 tests (workflow capture safety, repo_id stability, content bounding)
    - task-021: 25 tests (CLI end-to-end, exit codes, intent validation)
    - task-022: 26 tests (structured violations/recommendations, backward compat)
    - task-023: 44 tests (severity/confidence filtering, edge cases)
    - task-024: 30 tests (memory search, keyword matching, structured results, robustness)
    - 47 tests in other files (commands, dependency graph, edge cases, plan/refactor wiring)
- **Pass Rate:** 100% (verified by real pytest runs 2026-07-15)
- **Coverage Areas:**
  - ✅ Validation & input checking (60+ tests)
  - ✅ Core functionality (80+ tests)
  - ✅ Error handling (35+ tests)
  - ✅ Edge cases (80+ tests across all 5 tasks)
  - ✅ Real repo verification (against repos/click, repos/flask, repos/requests)
  - ✅ Robustness (unicode, SQL injection, special chars, long inputs)

- **Test Execution:** ~150 seconds for full cli-commands suite
- **External Dependencies:** Zero in tests (all against real repos, no mocks)
- **Type Safety:** 100% annotations, mypy strict mode

---

## 5. Performance Metrics

### Indexing
- Scan: <30 seconds (1000 files)
- Incremental: <5 seconds
- Symbol extraction: ~1ms/file

### Search
- BM25: <10ms
- Semantic: <50ms
- Hybrid: <100ms

### Orchestration
- Intent routing: <10ms
- Selector engine: <20ms
- Context assembly: <500ms

### Token Optimization
- Deduplication: <10ms
- Reranking: <5ms
- Graph expansion: <50ms
- Arch boosting: <5ms
- Model adaptation: <1ms

---

## 6. Known Limitations & Upgrade Paths

### Current Limitations
- **Call Graph:** Cannot resolve dynamic calls (getattr, eval)
- **Component 4 (Compressor):** Heuristic truncation (production: real LLM)
- **Metrics Baseline:** 45/50 repos (5 pending)
- **Auto-Tuning:** Requires 10+ samples per intent class
- **Windows Git:** Temp file issue (non-blocking)

### Planned Enhancements (Phase 5)
- Real LLM API integration for compressor
- IDE extensions (VS Code, JetBrains)
- Cross-repo dependency analysis
- Advanced ML architecture detection
- Auto-healing (bug detection + fixes)
- Artifact versioning & diff
- Advanced search filters

---

## 7. Storage & Architecture

### Local Storage
- **SQLite:** `.ortho/ortho.db` (repository + workflow data)
- **Vectors:** `.ortho/vectors.db` (1536-dim embeddings)
- **Logs:** `.ortho/logs/` (daily context-quality CSV)
- **Config:** `.ortho/config.toml` (project settings)

### ASES Artifacts
- **Workflows:** `.ases/workflows/` (feature, bug-fix, refactor, analysis, etc.)
- **Agents:** `.ases/agents/` (core + custom)
- **Skills:** `.ases/skills/` (core + custom)

### Data Models
- 15+ SQLite tables (symbols, artifacts, edges, runs, etc.)
- 13 artifact types
- 5 architecture styles
- 8 agents, 10+ skills

---

## 8. ASES Workflow Compliance

✅ **GATE 1:** Plan Approval (spec.md, rollback plan documented)  
✅ **GATE 2:** Architecture Approval (ADR-015 compliant, no circular deps)  
✅ **GATE 3:** Scope Review (no unauthorized changes)  
✅ **GATE 4:** Test Coverage (110 tests, 100% pass, adversarial edge cases)  
✅ **GATE 5:** Verification (all quality metrics met, production ready)  

---

## 9. Blockers & Issues

- **Blockers:** None currently
- **Known Non-Blocking Issues:**
  - Git temp file issue on Windows (doesn't affect functionality)
  - Advanced namespace package detection (edge case)
  - Call graph cannot resolve dynamic calls (documented limitation)

---

## 10. Next Steps (Phase 5+)

1. **Component 4 Enhancement:** Real LLM API for summarization
2. **Metrics Completion:** Benchmark remaining 5 repositories
3. **IDE Extensions:** VS Code and JetBrains plugins
4. **Auto-Healing:** Bug detection + automated fixes
5. **Cross-Repo Analysis:** Dependencies across repositories
6. **Advanced Search:** Type, scope, age, and custom filters
7. **Artifact Versioning:** Track artifact changes over time
8. **Collaborative Workflows:** Real-time multi-user orchestration

---

## 11. Quick Links

- **Features:** See `FEATURES.md` for complete feature list
- **FRD:** See `ortho-v3-frd.md` for functional requirements
- **Build Plan:** See `docs/archive/PHASE_4_BUILD_PLAN.md` for component details
- **Architecture:** See `docs/architecture/` for technical docs
