# Ortho — Project Memory

**Purpose:** Cross-session working memory. Authoritative for current state, active decisions, and known facts.  
**Last Updated:** 2026-07-21  

---

## What Is Ortho?

Ortho is a **local-first Engineering Decision Engine** — an intelligence layer that sits between a developer and their AI coding tool. It scans a repo, builds a knowledge base (call graphs, imports, architecture, technical debt), and answers:

- What architecture does this repo use?
- What violations exist right now?
- What will break if I change X?
- What's the right implementation approach?
- What did we decide/reject last time?

Every finding cites real, checkable evidence (never fabricated). The core differentiator is the **accept/reject feedback loop** — `ortho feedback` → next scan cites "Rejected before (date): <reason>" instead of repeating the same finding blindly.

**Positioning:** Engineering Intelligence for AI-assisted software development. Local-first is a deployment advantage (no source leaves your machine), not the product itself.

---

## Current State (as of 2026-07-21)

| Dimension | Status |
|---|---|
| Engineering | Feature-complete. All four vNext phases built and audited. |
| Test suite | 1375 passed / 3 failed (3 are pre-existing, documented arch-classifier benchmark gaps) |
| mypy --strict | Clean on all active packages. arch-intelligence has 106 legacy errors (documented, not blocking) |
| Blocker | **Pilot study** — 5 pilot companies needed. Not an engineering problem. |
| Next action | Pilot recruitment per `PILOT_READINESS.md` §14 |

---

## Architecture

```
apps/
  cli/          — TypeScript CLI entry point (ortho binary), pybridge.ts
  mcp-server/   — 10-tool MCP server (stdio-verified)
  api-server/   — FastAPI REST API

packages/
  repo-intelligence     — AST, symbols, call/import graphs, RepoGraphQueries
  context-hub           — SQLite (FTS5 BM25), ArtifactStore, workflow_run capture
  arch-intelligence     — Architecture detection (5 styles), ArchModelAdapter
  arch-guardrails       — Layer-boundary enforcement, ArchitectureEnforcer
  change-planner        — Blast-radius analysis, ChangePredictor
  decision-engine       — Multi-source decision synthesis, DecisionEngine
  feature-planner       — Feature implementation paths
  refactoring-advisor   — Bloat/coupling/cycle findings
  impact-analysis       — Impact scoring utilities
  orchestration         — ASES workflow executor, intent router, selector engine
  token-optimizer       — 9-component context pipeline (dedup, rerank, compress, etc.)
  cli-commands          — CliCommands Python bridge; DependencyGraphAdapter
  dashboard-generator   — Reporting utilities
```

**Storage (per repo, local):**
- `.ortho/ortho.db` — symbols, artifacts, workflow_run history
- `.ortho/vectors.db` — 1536-dim embeddings
- `.ortho/logs/` — context-quality CSV (daily rotation)
- `.ortho/config.toml` — project settings

---

## ADR Index

| ADR | Decision |
|---|---|
| ADR-004 | Storage: SQLite, local-first |
| ADR-005 | Language adapters as plugins |
| ADR-013 | Intent classification: semantic-router (HuggingFace encoder, <10ms, no LLM) |
| ADR-014 | Selector Engine: pure Python, deterministic (no LLM) |
| ADR-015 | Layer boundaries: one-way acyclic imports, enforced (`docs/architecture/adr-015-layer-boundaries.md`) |
| ADR-016 | Engineering Copilot layer: change-planner, feature-planner, refactoring-advisor, arch-guardrails, decision-engine live between Apps and Intelligence |

---

## CLI Commands

```bash
# Bootstrap
ortho init
ortho scan                          # full repo index (~10-30s for 1000 files)
ortho index --since <ref>           # incremental git-diff-based re-index

# ContextHub
ortho context add/search/list/stats

# Analysis
ortho analyze [--impact|--debt|--deps]

# Engineering Copilot (the core product)
ortho guardrails [path] [--severity error|warning]
ortho decide <intent> [--scan-path PATH] [--confidence 0.0-1.0]
ortho plan <intent> [--scan-path PATH]
ortho refactor [path]

# Intelligence
ortho ask <question>                # repo Q&A (graph-grounded, never fabricates)
ortho cross-repo                    # cross-repo intelligence (fails fast >2000 pooled symbols)
ortho orchestrate                   # workflow orchestration (never auto-approves)

# Memory & Feedback
ortho feedback                      # accept/reject loop; persists to .ortho/ortho.db
ortho memory search <query>         # BM25 over past workflow_run artifacts

# ASES Workflow
ortho run / status / approve / reject / history
ortho debug run/context
```

---

## Known Gaps & Limitations

| Gap | Severity | Status |
|---|---|---|
| `layer_boundaries` never fires on real repos | Medium | Synthetic-fixture proof only. Real-repo validation needed during pilot. |
| `cross-repo` O(n²) cliff at >2000 pooled symbols | Medium | Guarded — fails fast with actionable message. |
| arch-intelligence 106 mypy errors | Low | Legacy code, pre-dates strict mode. Documented. |
| arch-detection accuracy 75% on Python 3.14 repos | Medium | `repos/sqlalchemy` vendor uses 3.14 syntax the parser can't handle. Tracked, not fixed. |
| feature-planner intent-classification miss on non-web repos | Low | Documented gap. |
| Task-015: 45/50 benchmark repos (5 missing) | Low | Phase 5 mitigation. |
| Component 4 (Compressor): heuristic truncation only | Low | Production would use real LLM API. |

---

## Development Rules (Non-Negotiable)

1. **ASES workflow mandatory** for every feature: PLANNER → ARCHITECT → BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER
2. **No simulated metrics or logs** — pytest MUST be executed, GATE 5 requires human spot-check of actual exit codes
3. **mypy --strict** on all new Python; no `any` in TypeScript
4. **All benchmarks must be reproducible** with hand-authored ground truth
5. **Local-first** — no cloud, no auth, SQLite only
6. **spec.md before implementation** — expected test metrics documented first

---

## ICP (Ideal Customer Profile)

- 30–300 engineers, multiple teams sharing a codebase
- Already shipping AI-generated code (Copilot, Claude Code, Cursor) at volume
- Structural reason code can't leave their infrastructure: SOC2/HIPAA/FedRAMP, IP, contractual
- Existing architecture worth protecting (non-trivial, layered/modular)
- Local-first is how they're *allowed* to buy AI code review at all — competitors (CodeRabbit, Greptile, Qodo) are structurally disqualified

---

## Key Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | AI working context (this session's instructions) |
| `memory.md` | This file — cross-session facts |
| `status.md` | Detailed per-task historical status |
| `PILOT_READINESS.md` | Business/GTM strategy, ICP, pilot plan |
| `PRODUCT_POSITIONING.md` | One-page product pitch |
| `ortho-v3-frd.md` | Full functional requirements |
| `FEATURES.md` | Complete feature list |
| `docs/architecture/adr-015-layer-boundaries.md` | Layer boundary rules |
| `docs/archive/PRODUCTION_AUDIT_2026-07-15.md` | Production readiness audit detail |
| `docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md` | False-positive reduction audit |
| `.ases/` | ASES workflow state, gate checklists, task archives |
| `ortho-demo/` | Demo project (separate README/ROADMAP) |
| `repos/` | Vendored benchmark repos (click, flask, requests, sqlalchemy, etc.) |

---

## Completed Milestones (Reverse Chronological)

| Date | Milestone |
|---|---|
| 2026-07-16 | vNext Phase 4 + full independent audit. 1375 tests, zero new regressions. |
| 2026-07-16 | False-positive audit: 91%→0% verified FP rate on 9-repo hand-audit |
| 2026-07-15 | Tasks 020–024: ContextHub capture, CLI copilot exposure, structured JSON output, severity/confidence filtering, memory search |
| 2026-07-15 | Production Readiness Audit: fixed critical install bug, broken imports, unbounded-scan regression |
| 2026-07-14 | Task-017: Real CLI wiring — `guardrails`/`decide` replaced 100% stub output with real engine calls |
| 2026-07-12 | Codebase cleanup: orphaned dirs, gitignore, ADR-015, `__all__` exports |
| Earlier | Phases 1–6: foundation, repo intelligence, orchestration, arch intelligence, token optimizer, engineering benchmarks |
