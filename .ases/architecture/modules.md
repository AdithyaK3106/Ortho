# Module Map

**Last Updated:** 2026-06-27 00:20 UTC  
**Maintainer:** ARCHITECT

This file documents the system's module boundaries, dependencies, and API contracts. Updated by the ARCHITECT whenever a new module is introduced or boundaries change.

---

## Top-Level Modules

### 1. ASES (AI Software Engineering System)

**Status:** Phase 0 (Bootstrap — Tasks 001-009 in progress)  
**Owner:** Solo developer (all agents)  
**Location:** `.ases/`  
**Maintainer:** ARCHITECT

**Purpose:** Multi-agent orchestration framework for disciplined software engineering under ASES governance (ADR-001).

**Core Submodules:**
- **agents/** (6 files, 2,065 lines)
  - planner.md, architect.md, builder.md, test-designer.md, verifier.md, reviewer.md
  
- **workflows/** (4 files, 1,438 lines)
  - feature.md, bugfix.md, baseline-audit.md, bootstrap.md
  
- **templates/** (10 files, 2,301 lines)
  - plan.md, spec.md, rollback-plan.md, architecture-review.md, implementation-notes.md, test-plan.md, verification-report.md, evidence-package.md, review.md, adr.md
  
- **architecture/** (4+ files)
  - decisions.md, modules.md, contracts.md, adrs/ (INDEX.md + 3 ADRs)
  
- **commands/** (4 files, TBD)
  - verify-ts.sh, verify-python.sh, verify-android.sh, capture-evidence.sh
  
- **evidence/** — Terminal output logs (read-only)
  - baseline/ — Baseline audit logs
  - [task-id]/ — Per-task logs
  
- **tasks/** — Per-task artifacts (created during Phase 2+)

---

### 2. Ortho (Planned — Phase 2+)

**Status:** Not yet started  
**Owner:** Solo developer (under ASES governance)  
**Location:** `./ortho/` (TBD)  
**Dependencies:** ASES (governance, workflows, templates)

**Purpose:** AI software engineering assistant — core language model integration system.

**Planned Top-Level Submodules:**
- `core/` — LLM integration and reasoning engine
- `analysis/` — Code analysis and metrics
- `generation/` — Code generation and suggestions
- `ui/` — CLI/web interface

**Stack:** TypeScript (primary) + Python (data/ML, optional)

**Development:** All Ortho features will follow ASES workflow (feature.md or bugfix.md) starting Phase 2.

---

### 3. Expense App (Planned — Phase 3+)

**Status:** Not yet started  
**Owner:** Solo developer (under ASES governance)  
**Location:** `./expense-app/` (TBD)  
**Dependencies:** ASES (governance, workflows, templates)

**Purpose:** Personal expense tracking application (Android mobile + backend).

**Planned Top-Level Submodules:**
- `app/` — Android application
- `backend/` — API server (TBD)
- `data/` — Database schema and migrations

**Stack:** Kotlin/Java + Gradle (Android), TypeScript/Node (backend, TBD)

**Development:** All Expense App features will follow ASES workflow starting Phase 3.

---

## Dependency Graph

```
Phase 0 (Bootstrap):
  ASES (self-contained, no external dependencies)

Phase 2+ (Active Development):
  Ortho → ASES (governance)
  Expense App → ASES (governance)
  
No circular dependencies. ASES is foundation, projects build on top.
```

---

## Module Boundaries and Responsibilities

### ASES Module Responsibility
- Orchestrate multi-agent engineering workflows
- Maintain evidence and verification logs
- Track task state and gate approvals
- Persist decisions in ADRs
- Provide templates and prompts for all phases

### Ortho Module Responsibility (Phase 2+)
- Implement LLM-based code assistance
- Analyze code for improvements
- Generate code suggestions
- Provide CLI/UI for interaction

### Expense App Module Responsibility (Phase 3+)
- Track user expenses
- Manage expense categories
- Provide mobile UI (Android)
- Provide API backend

---

## API Contracts

### ASES Workflow API (internal)
Interfaces between agent roles (defined in workflows/):

- PLANNER outputs → ARCHITECT inputs
  - Provides: plan.md, spec.md, rollback-plan.md
  - Format: Markdown files in `.ases/tasks/[task-id]/`

- ARCHITECT outputs → BUILDER inputs
  - Provides: architecture-review.md, optional ADRs
  - Format: Markdown files in `.ases/tasks/[task-id]/`

- BUILDER outputs → TEST-DESIGNER inputs
  - Provides: production code, implementation-notes.md
  - Format: Code files + markdown in project root and `.ases/tasks/[task-id]/`

- TEST-DESIGNER outputs → VERIFIER inputs
  - Provides: test files, test-plan.md
  - Format: Test files in project + markdown in `.ases/tasks/[task-id]/`

- VERIFIER outputs → REVIEWER inputs
  - Provides: verification-report.md, evidence-package.md, evidence log files
  - Format: Markdown + log files in `.ases/evidence/[task-id]/` and `.ases/tasks/[task-id]/`

- REVIEWER outputs → HUMAN inputs
  - Provides: review.md
  - Format: Markdown in `.ases/tasks/[task-id]/`

### Ortho APIs (Phase 2+)
To be defined when first Ortho feature is planned. Will follow ASES workflow.

### Expense App APIs (Phase 3+)
To be defined when first Expense App feature is planned. Will follow ASES workflow.

---

## Known Limitations

1. **ASES is solo-developer only** — Current design assumes one developer playing all roles (via session isolation). To scale to teams, would need to support concurrent BUILDER/TEST-DESIGNER/REVIEWER sessions.

2. **Android UI verification gap** — Expense App will lack automated UI testing (requires emulator). Must document as MANUAL-REQUIRED in verification reports.

3. **No CI/CD integration yet** — Phase 0 uses manual verification only. Phase 2 can add GitHub Actions/GitLab CI for automated evidence collection.

4. **Bootstrap is less rigorous** — Phase 0 uses five-rule protocol instead of full five-gate workflow (ADR-002 rationale).

---

## Transition Points

**Phase 0 → Phase 1:** 
- Baseline audit of Ortho (if it existed) or acceptance of starting point

**Phase 1 → Phase 2:**
- First feature of Ortho under full ASES governance

**Phase 2 → Phase 3:**
- First feature of Expense App under full ASES governance

---

*End of modules.md*
