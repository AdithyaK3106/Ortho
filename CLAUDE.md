# Ortho v3 — Project Status & Context

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 1 — Foundation (Weeks 1–8, started 2026-06-30)  
**Methodology:** ASES (AI Software Engineering System)  
**Stack:** Python (packages) + TypeScript (CLI)  
**FRD:** `ortho-v3-frd.md` (sections 1–18, authoritative)  
**Last Updated:** 2026-06-30 by PLANNER

---

## Project Overview

Building Ortho from scratch using ASES workflows. Every task follows: `.ases/workflows/feature.md` → 6 gates, 10 artifacts, human approval at each stage.

**Current Status:** BUILDING (task-001 BUILDER phase — implementing 9 atomic tasks)

---

## Current Phase: Phase 1 (Foundation)

**Goal:** CLI that scans a Python repo and makes its contents searchable. No AI yet.

**Timeline:** Weeks 1–8 (estimated completion: 2026-08-24)

### Week 1–2: Shared Foundation (CURRENT)
- [ ] Monorepo + Poetry workspaces
- [ ] Shared types (TypeScript + Python dataclasses)
- [ ] SQLite storage layer with migrations
- [ ] `.ortho/` directory structure + config
- [ ] CLI skeleton with `ortho init`
- [ ] FastAPI server skeleton
- [ ] ADR-001 (storage strategy)
- [ ] ADR-002 (language adapter plugin model)

### Week 3–4: Repo Intelligence — Python (Not started)
- [ ] LanguageAdapter interface
- [ ] Python AST adapter (tree-sitter + astchunk)
- [ ] Symbol extraction + registry
- [ ] Import graph builder
- [ ] `ortho scan` command

### Week 5–6: Repo Intelligence — Call Graph + Incremental (Not started)
- [ ] Call graph builder (pyan3)
- [ ] Dependency graph (requirements.txt, pyproject.toml)
- [ ] Module detector
- [ ] Incremental indexer (git diff based)
- [ ] `ortho index --watch`

### Week 7–8: ContextHub (Not started)
- [ ] Artifact store + ingestion contract
- [ ] BM25 search (FTS5)
- [ ] Semantic search (sqlite-vec)
- [ ] Hybrid RRF search
- [ ] Git metadata store
- [ ] Project memory
- [ ] `ortho context add/search`

---

## Active Tasks

### task-001: Shared Foundation

**State:** READY-FOR-GATE-2-APPROVAL  
**Workflow:** `.ases/workflows/feature.md`  
**Started:** 2026-06-30

**Artifacts Completed:**
- ✅ `.ases/tasks/task-001-shared-foundation/plan.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-001-shared-foundation/spec.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-001-shared-foundation/rollback-plan.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-001-shared-foundation/architecture-review.md` (ARCHITECT complete, GATE 2: approval pending)
- ✅ `.ases/architecture/adrs/ADR-004-storage-strategy-sqlite-local-first.md` (PROPOSED status)
- ✅ `.ases/architecture/adrs/ADR-005-language-adapter-plugin-model.md` (PROPOSED status)

**GATE 2: APPROVED** ✅ (2026-06-30 12:00 UTC)

ADRs status updated:
- ADR-004: ACCEPTED (Storage Strategy)
- ADR-005: ACCEPTED (Language Adapter Plugin Model)

**Next Step:** BUILDER implements 9 atomic tasks in order:
1. Monorepo structure + Poetry setup
2. Shared types (TypeScript)
3. SQLite storage layer (Python)
4. SQLite schema + migrations
5. OrthoConfig + .ortho/ directory
6. CLI skeleton + `ortho init`
7. FastAPI server skeleton
8. ADR-001 (storage strategy) — already written
9. ADR-002 (language adapter) — already written

**After implementation:** BUILDER produces implementation-notes.md documenting what was built, deviations, scope violations (if any)

---

## Completed Tasks

None yet.

---

## Blockers

None currently.

---

## Architecture Decisions (ADRs)

| ADR | Title | Status | Created |
|-----|-------|--------|---------|
| ADR-001 | Storage Strategy (SQLite + sqlite-vec) | DRAFT (will be written by ARCHITECT in task-001) | TBD |
| ADR-002 | Language Adapter Plugin Model | DRAFT (will be written by ARCHITECT in task-001) | TBD |

---

## Key Decisions Made

1. **Methodology:** Using ASES full workflow (no shortcuts), even for Phase 1 infrastructure
2. **No direct coding:** Every feature goes through PLANNER → ARCHITECT → BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER
3. **Evidence over confidence:** All claims backed by logs, test output, type checking results
4. **Local-first:** No cloud, no auth, SQLite only
5. **Type safety:** Strict TypeScript (no `any`), mypy --strict for Python

---

## Notes for Next Session

**For ARCHITECT role (after human approves plan):**
- Review `.ases/tasks/task-001-shared-foundation/spec.md` carefully
- Check schema from FRD Section 14 line-by-line
- Verify no circular dependencies between packages
- Ensure CLI → API → Storage data flow is correct
- Write ADR-001 (storage strategy) and ADR-002 (plugin model)
- Produce `architecture-review.md` with verdict: APPROVED or REJECTED
- **Gate 2 approval required** before BUILDER proceeds

**For BUILDER role (after human approves architecture):**
- **CRITICAL:** Read `rollback-plan.md` FIRST
- Read `spec.md` to understand exact scope
- Implement 9 atomic tasks in order (dependencies matter)
- Test as you go (build, lint, type check on each commit)
- Produce `implementation-notes.md` documenting what was built, what wasn't, any deviations
- Commit each atomic task (granular history for potential rollback)

**For TEST-DESIGNER role (fresh session, independent):**
- Don't look at BUILDER's code until review phase
- Read `spec.md` and `implementation-notes.md` only
- Write tests for all 20 acceptance criteria
- Test CLI → API → Storage integration end-to-end
- Cover edge cases (missing config, bad database, etc.)

**For VERIFIER role:**
- Mode A: Run `./.ases/commands/capture-evidence.sh task-001 all`
- Mode B: Read logs, compare to spec, produce verification report
- Check: Build ✓, Types ✓, Lint ✓, Tests ✓, Regression ✓

**For REVIEWER role (fresh session, independent):**
- Don't see BUILDER's work until now
- Read spec, implementation notes, test plan, verification report
- Ask 7 adversarial questions from `.ases/GATE-CHECKLIST.md`
- Produce review.md with verdict: APPROVED or REJECTED

---

## Evidence Files Location

All evidence (logs, reports, artifacts) stored in:
```
.ases/tasks/task-001-shared-foundation/
├── plan.md
├── spec.md
├── rollback-plan.md
├── architecture-review.md (created by ARCHITECT)
├── implementation-notes.md (created by BUILDER)
├── test-plan.md (created by TEST-DESIGNER)
├── verification-report.md (created by VERIFIER)
├── evidence-package.md (created by VERIFIER)
└── review.md (created by REVIEWER)

.ases/evidence/task-001/
├── build-*.log (tsc, mypy)
├── lint-*.log (eslint)
├── test-*.log (if any)
└── regression-*.log (if any)
```

---

## Dependency Map (for reference)

```
CLI → API-Server → Storage → Shared Types
       (TypeScript)  (Python)  (TS + Python)

Package structure:
packages/
  ├── repo-intelligence/ (Week 3–4)
  ├── context-hub/ (Week 7–8)
  ├── arch-intelligence/ (Phase 2)
  ├── orchestration/ (Phase 3)
  └── token-optimizer/ (Phase 4)

shared/
  ├── types/ (Week 1–2, THIS WEEK)
  ├── storage/ (Week 1–2, THIS WEEK)
  └── utils/

apps/
  ├── cli/ (Week 1–2, THIS WEEK)
  └── api-server/ (Week 1–2, THIS WEEK)
```

---

## Verification Status

**Phase 1 Week 1–2 (task-001):**
- Build: Not started
- Types: Not started
- Lint: Not started
- Tests: Not started
- Integration: Not started

---

## External References

| Resource | Purpose | Link |
|----------|---------|------|
| FRD | Ortho specification (source of truth) | `ortho-v3-frd.md` |
| Feature Workflow | ASES workflow for features | `.ases/workflows/feature.md` |
| Quick Start | ASES quick reference | `.ases/QUICK-START.md` |
| Status Tracker | Phase progress | `status.md` |

---

## Team (Solo Developer)

- **Role:** PLANNER → ARCHITECT → BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER
- **Context:** All ASES workflows, FRD, CLAUDE.md
- **Constraints:** One person, multiple roles, must use ASES discipline

---

## How to Continue

1. **If you're the HUMAN:** Review `.ases/tasks/task-001-shared-foundation/` (plan, spec, rollback). Check the gate checklist above. Approve or send back.

2. **If you're ARCHITECT (after human approves):** Read `.ases/agents/architect.md`, then review spec against FRD. Write `architecture-review.md` + ADRs.

3. **If you're BUILDER (after human approves architecture):** Read `.ases/agents/builder.md`, **read rollback-plan.md FIRST**, implement 9 atomic tasks in order.

4. **If you're TEST-DESIGNER (after human approves scope):** Fresh session. Read `.ases/agents/test-designer.md`. Write tests for all 20 acceptance criteria.

5. **If you're VERIFIER (after human approves test plan):** Run evidence capture, produce reports.

6. **If you're REVIEWER (after human approves evidence):** Fresh session. Read code, write review.md.

---

*Last updated: 2026-06-30 11:15 UTC by PLANNER*  
*Next update: ARCHITECT to review and document architecture decisions*

---

## Ponytail Status

**Mode:** FULL (lazy efficiency enforced — stdlib over custom code, native before deps, shortest diff that works)

This means:
- No over-engineering during implementation
- Minimal dependencies (only what FRD specifies)
- Question every new file/module (YAGNI principle)
- Mark intentional shortcuts with `# ponytail:` comments

---

---

*Last updated: 2026-06-30 11:45 UTC by ARCHITECT (architecture review complete, awaiting GATE 2 approval)*

*End of CLAUDE.md*
