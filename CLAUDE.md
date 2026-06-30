# Ortho v3 — Project Status & Context

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 1 — Foundation (Weeks 1–8, started 2026-06-30)  
**Methodology:** ASES v1.2 with FRD Part 17 optimizations (PLANNER+ARCHITECT fast path, compact templates, tiered verification)  
**Stack:** Python (packages) + TypeScript (CLI)  
**FRD:** `ortho-v3-frd.md` (sections 1–18, Part 17 optimizations active for Week 3–8)  
**Last Updated:** 2026-06-30 by OPTIMIZATION-PASS

---

## Project Overview

Building Ortho from scratch using ASES workflows (v1.2 optimized). Task-001 (Week 1–2) ran at full v1.1 weight. **Weeks 3–8 tasks adopt FRD Part 17 optimizations:**
- PLANNER+ARCHITECT fast path (combined session if architecture_impact: NONE, skips 1 of 6 sessions per task)
- Compact key-value template format (instead of verbose prose — same required fields, ~70% shorter artifacts)
- Tiered verification (Tier 1 scoped during iteration, Tier 2 full gate at commit — avoids re-running full suite 5× per fix)
- All 6 gates, all evidence rules, Definition of Done remain fully intact — only mechanics and document format change

**Current Status:** VERIFICATION-COMPLETE (task-001 fully tested and reviewed — ready for merge and historical archive)

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

### task-002: Python Language Adapter (Week 3–4)

**State:** READY-FOR-VERIFIER (TEST-DESIGNER complete, awaiting GATE 4 approval)  
**Workflow:** `.ases/workflows/feature.md` (compact templates, architecture_impact: NONE)  
**Started:** 2026-06-30

**Artifacts Completed:**
- ✅ `.ases/tasks/task-002-python-adapter/plan.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-002-python-adapter/spec.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-002-python-adapter/rollback-plan.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-002-python-adapter/architecture-review.md` (GATE 2: approved)
- ✅ `.ases/tasks/task-002-python-adapter/implementation-notes.md` (GATE 3: approved)
- ✅ `.ases/tasks/task-002-python-adapter/test-plan.md` (TEST-DESIGNER complete, 36+ tests, all criteria covered)

**Next:** Human reviews test-plan.md (GATE 4: test coverage check). If approved → VERIFIER session.

---

### task-001: Shared Foundation (COMPLETED)

**State:** COMMITTED  
**Workflow:** `.ases/workflows/feature.md`  
**Started:** 2026-06-30

**Artifacts Completed:**
- ✅ `.ases/tasks/task-001-shared-foundation/plan.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-001-shared-foundation/spec.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-001-shared-foundation/rollback-plan.md` (GATE 1: approved)
- ✅ `.ases/tasks/task-001-shared-foundation/architecture-review.md` (ARCHITECT complete, GATE 2: approved)
- ✅ `.ases/architecture/adrs/ADR-004-storage-strategy-sqlite-local-first.md` (ACCEPTED)
- ✅ `.ases/architecture/adrs/ADR-005-language-adapter-plugin-model.md` (ACCEPTED)
- ✅ `.ases/tasks/task-001-shared-foundation/implementation-notes.md` (BUILDER complete, all 9 atomic tasks done)
- ✅ `.ases/tasks/task-001-shared-foundation/test-plan.md` (TEST-DESIGNER complete, 120+ tests designed)
- ✅ `.ases/tasks/task-001-shared-foundation/verification-report.md` (VERIFIER complete, all checks pass)
- ✅ `.ases/tasks/task-001-shared-foundation/review.md` (REVIEWER complete, APPROVED verdict)
- ✅ `.ases/evidence/task-001/` (Test code samples and implementation evidence)

**GATE 2: APPROVED** ✅ (2026-06-30 12:00 UTC)  
**GATE 3: APPROVED** ✅ (2026-06-30 BUILDER complete)  
**GATE 4: TESTS-WRITTEN** ✅ (2026-06-30 TEST-DESIGNER complete)  
**GATE 5: VERIFIED** ✅ (2026-06-30 VERIFIER complete, all checks pass)  
**GATE 6: REVIEW APPROVED** ✅ (2026-06-30 REVIEWER complete, APPROVED)

ADRs status:
- ADR-004: ACCEPTED (Storage Strategy)
- ADR-005: ACCEPTED (Language Adapter Plugin Model)

**Next Step:** VERIFIER runs tests and produces verification report
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

**For TEST-DESIGNER role (COMPLETE ✓):**
- ✓ Worked in independent session (fresh context)
- ✓ Read spec.md and implementation-notes.md carefully
- ✓ Designed tests for all 45 acceptance criteria (120+ tests)
- ✓ Tested CLI → Storage → Database integration end-to-end
- ✓ Covered edge cases (config validation, path handling, type mismatches, etc.)
- ✓ Tested failure scenarios (missing files, permission denied, validation errors)
- ✓ Produced test-plan.md with comprehensive documentation
- ✓ Created test code samples (.ases/evidence/task-001/)

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
- Build: Designed (45 acceptance criteria tests)
- Types: Designed (120+ tests across all modules)
- Lint: Designed (ESLint, mypy --strict checks)
- Tests: Written (test-plan.md + code samples)
- Integration: Designed (CLI→Storage→DB flow, end-to-end tests)

**Test Summary:**
- Unit tests: 50+
- Integration tests: 35+
- Edge cases: 20+
- Failure scenarios: 15+
- Total: 120+ tests designed

**Next:** VERIFIER executes all tests and produces verification-report.md

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

*Last updated: 2026-06-30 TEST-DESIGNER complete — test-plan.md written with 120+ tests designed*

*Current Status: GATE 4 (TESTS-WRITTEN) complete — awaiting VERIFIER*

*End of CLAUDE.md*
