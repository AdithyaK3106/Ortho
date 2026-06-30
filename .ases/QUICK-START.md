# ASES Quick Start — First-Time User Guide

**You have 5 minutes. This guide gets you started.**

---

## What is ASES?

ASES is an AI Software Engineering System that enforces disciplined development through:
- **Role separation:** Different agents (PLANNER, ARCHITECT, BUILDER, etc.) working in sequence
- **Evidence gating:** No task proceeds without proof (test results, type checking, etc.)
- **Honest uncertainty:** Agents document gaps honestly instead of fabricating confidence

Think: structured engineering team inside a single Claude session.

---

## Before You Start

1. **Read CLAUDE.md** (5 min) — understands the phase, stack, and current status
2. **Read the appropriate agent prompt** (5 min) — if you're a PLANNER, read `.ases/agents/planner.md`, etc.
3. **Copy a template** (1 min) — if you're starting a task, copy a template from `.ases/templates/` to your task folder
4. **Check the state machine** (2 min) — read `.ases/state-machine.md` to understand what state you're in

---

## I'm Starting a New Feature

**Timeline:** ~3 hours for a small feature (register/login)

### Step 1: Create Task Folder
```bash
mkdir -p .ases/tasks/task-feature-auth
```

### Step 2: You Are PLANNER
- [ ] Read `.ases/agents/planner.md` — understand your role
- [ ] Copy `.ases/templates/plan.md` to `.ases/tasks/task-feature-auth/plan.md`
- [ ] Copy `.ases/templates/spec.md` to `.ases/tasks/task-feature-auth/spec.md`
- [ ] Copy `.ases/templates/rollback-plan.md` to `.ases/tasks/task-feature-auth/rollback-plan.md`
- [ ] Fill in all three documents (follow templates exactly)
- [ ] Commit: `git add .ases/tasks/task-feature-auth/ && git commit -m "task-feature-auth: Planning complete"`
- [ ] Update CLAUDE.md: mark task state as READY-FOR-ARCHITECT

### Step 3: Human Reviews (You, Wearing Reviewer Hat)
- [ ] Read plan, spec, rollback
- [ ] Check: acceptance criteria are testable (binary pass/fail, not "should work")
- [ ] Approve or reject
- [ ] Update CLAUDE.md: task → ARCHITECTURE-REVIEW (if approved)

### Step 4: You Are ARCHITECT
- [ ] Read `.ases/agents/architect.md`
- [ ] Copy `.ases/templates/architecture-review.md` to `.ases/tasks/task-feature-auth/`
- [ ] Analyze module boundaries, dependencies, API contracts
- [ ] Write architecture-review.md with verdict: APPROVED or REJECTED
- [ ] Commit with message: `task-feature-auth: Architecture review complete`
- [ ] Update CLAUDE.md: task → READY-FOR-BUILDER

### Step 5: Human Reviews Again
- [ ] Read architecture-review.md
- [ ] Check: module boundaries clear, contracts explicit, risks identified
- [ ] Approve or reject
- [ ] Update CLAUDE.md: task → BUILDING (if approved)

### Step 6: You Are BUILDER
- [ ] Read `.ases/agents/builder.md`
- [ ] **CRITICAL:** Read rollback-plan.md first
- [ ] Read spec.md to understand what to build
- [ ] Implement the code
- [ ] Copy `.ases/templates/implementation-notes.md` to `.ases/tasks/task-feature-auth/`
- [ ] Fill in: what was built, what wasn't, files modified, deviations
- [ ] Commit code and implementation-notes.md with message: `task-feature-auth: Implementation complete`
- [ ] Update CLAUDE.md: task → READY-FOR-TEST-DESIGNER

### Step 7: Human Reviews
- [ ] Read implementation-notes.md and skim code
- [ ] Check: code is syntactically correct, no obvious bugs, rollback plan was read
- [ ] Approve or reject
- [ ] Update CLAUDE.md: task → TEST-DESIGN (if approved)

### Step 8: **NEW SESSION** — You Are TEST-DESIGNER
- [ ] Read `.ases/agents/test-designer.md`
- [ ] **CRITICAL:** Do not access prior session state; you're independent
- [ ] Copy `.ases/templates/test-plan.md` to `.ases/tasks/task-feature-auth/`
- [ ] Read spec.md and implementation-notes.md only
- [ ] Design tests for every acceptance criterion
- [ ] Write test code
- [ ] Commit with message: `task-feature-auth: Test design complete`
- [ ] Update CLAUDE.md: task → READY-FOR-VERIFIER

### Step 9: Human Reviews
- [ ] Read test-plan.md
- [ ] Check: every acceptance criterion has a test, edge cases listed, regression candidates noted
- [ ] Approve or reject
- [ ] Update CLAUDE.md: task → VERIFICATION-MODE-A (if approved)

### Step 10: You Are VERIFIER (Mode A)
- [ ] Read `.ases/agents/verifier.md` (Mode A section)
- [ ] Run: `./.ases/commands/capture-evidence.sh task-feature-auth typescript`
- [ ] Wait for all evidence logs to be created in `.ases/evidence/task-feature-auth/`
- [ ] Proceed to Mode B (same session)

### Step 11: You Are VERIFIER (Mode B)
- [ ] Read `.ases/agents/verifier.md` (Mode B section)
- [ ] Copy `.ases/templates/verification-report.md` to `.ases/tasks/task-feature-auth/`
- [ ] Copy `.ases/templates/evidence-package.md` to `.ases/tasks/task-feature-auth/`
- [ ] Read each evidence log file and quote exact error/success lines
- [ ] Fill verification-report.md: what passed, what failed, gaps documented
- [ ] Fill evidence-package.md: gates checklist, known limitations, ready-for-review verdict
- [ ] Commit with message: `task-feature-auth: Verification complete`
- [ ] Update CLAUDE.md: task → READY-FOR-REVIEWER

### Step 12: Human Reviews
- [ ] Read verification-report.md and evidence-package.md
- [ ] Check: all tests passed, no evidence gaps, ready-for-review = YES
- [ ] Approve or reject
- [ ] Update CLAUDE.md: task → REVIEW (if approved)

### Step 13: **NEW SESSION** — You Are REVIEWER
- [ ] Read `.ases/agents/reviewer.md`
- [ ] **CRITICAL:** Do not access prior session state; you're independent
- [ ] Copy `.ases/templates/review.md` to `.ases/tasks/task-feature-auth/`
- [ ] Read: spec.md, implementation-notes.md, test-plan.md, verification-report.md
- [ ] Ask all 7 adversarial questions (see `.ases/GATE-CHECKLIST.md`)
- [ ] Write review.md with verdict: APPROVED or REJECTED
- [ ] Commit with message: `task-feature-auth: Final review complete`
- [ ] Update CLAUDE.md: task → READY-FOR-RELEASE (if APPROVED)

### Step 14: Human Final Sign-Off
- [ ] Read review.md
- [ ] Check: all 7 questions answered, verdict is APPROVED
- [ ] Approve or reject
- [ ] Update CLAUDE.md: task → COMPLETED (if approved)

**Task done.** All 10 artifacts in `.ases/tasks/task-feature-auth/`.

---

## I'm Fixing a Bug

**Timeline:** ~1 hour for a small bug (missing error check)

### Simplified Workflow (Skip ARCHITECT if not needed)
1. PLANNER: plan.md, spec.md, rollback-plan.md
2. Human review (Gate 1)
3. ARCHITECT: architecture-review.md (often: "no architectural change needed")
4. Human review (Gate 2)
5. BUILDER: code, implementation-notes.md
6. Human review (Gate 3)
7. TEST-DESIGNER (NEW SESSION): test-plan.md, tests
8. Human review (Gate 4)
9. VERIFIER (Mode A+B): evidence, reports
10. Human review (Gate 5)
11. REVIEWER (NEW SESSION): review.md
12. Human final sign-off (Gate 6)

Same 6 gates, same 10 artifacts. Bugfixes usually move faster because scope is smaller.

---

## I'm Auditing Existing Code (Brownfield)

**Timeline:** ~4 hours for baseline audit (TypeScript project)

### Baseline Audit Workflow
- Read `.ases/workflows/baseline-audit.md`
- ARCHITECT: existing code → architecture-review.md
- TEST-DESIGNER: existing code → test-plan.md + new tests
- VERIFIER: run evidence capture on existing + new tests
- REVIEWER: assess code quality, documentation, tech debt

No BUILDER in baseline audit (code already exists). Produce `.ases/baseline/` artifacts.

---

## How Do I Know What to Do?

**Always read these in order:**

1. **CLAUDE.md** — current phase, stack, what tasks are active
2. **Your agent prompt** — `.ases/agents/[role].md` — what you do, what you read, what you write
3. **Your template** — `.ases/templates/[artifact].md` — what to fill in
4. **State machine** — `.ases/state-machine.md` — what state are we in, what's next
5. **Gate checklist** — `.ases/GATE-CHECKLIST.md` — what does approval require

If stuck: read `.ases/task-template.md` for the full checklist of your role.

---

## Common Questions

**Q: Can I skip the rollback plan?**  
No. BUILDER must read rollback-plan.md before writing code. Non-negotiable.

**Q: Can I do BUILDER and TEST-DESIGNER in the same session?**  
No. They must be separate sessions. TEST-DESIGNER doesn't see BUILDER's work until the review phase.

**Q: What if I'm rejected at a gate?**  
Read the human feedback. Fix the artifact. Re-submit. Approval required to proceed.

**Q: Do I have to run all 5 verification scripts?**  
No. Run the stack that applies: TypeScript, Python, or Android. Or run `all` if you have multiple stacks.

**Q: What if a tool is missing (e.g., `pytest` not installed)?**  
The script logs "pytest not found". That's fine. Document it in the verification-report.md as a limitation. Proceed to review.

**Q: Can I edit evidence logs?**  
No. Evidence logs come from tools only. If you see a problem, re-run the tools. Never hand-edit logs.

**Q: What if tests fail?**  
Document exact failure in verification-report.md. Return to BUILDER to fix code. Re-run verification. Gate is not passed until tests pass.

---

## Verification Commands (Quick Ref)

```bash
# TypeScript (Ortho)
./.ases/commands/capture-evidence.sh task-feature-auth typescript

# Python (Ortho variant)
./.ases/commands/capture-evidence.sh task-feature-auth python

# Android (Expense App)
./.ases/commands/capture-evidence.sh task-feature-auth android

# All stacks
./.ases/commands/capture-evidence.sh task-feature-auth all
```

Evidence logs go to: `.ases/evidence/task-feature-auth/`

---

## Glossary

| Term | Meaning |
|------|---------|
| **Agent** | A role: PLANNER, ARCHITECT, BUILDER, TEST-DESIGNER, VERIFIER, REVIEWER |
| **Gate** | An approval point (Gates 1–6). Task cannot proceed until gate passes. |
| **Artifact** | A document produced by an agent: plan.md, spec.md, review.md, etc. |
| **Evidence** | Terminal output from tools (tsc, jest, gradle): build logs, test results, lint output. |
| **State** | Current position in task lifecycle: PLANNING, BUILDING, VERIFICATION-MODE-A, etc. |
| **Phase** | BOOTSTRAP (Phase 0 = building ASES), or Phase 2+ (using ASES for real work) |

---

## File Structure (Reminder)

```
.ases/
├── agents/              ← Agent prompts (read first in your role)
├── templates/           ← Copy-paste templates for artifacts
├── workflows/           ← Workflow definitions (feature, bugfix, baseline, bootstrap)
├── commands/            ← Verification scripts (.sh files)
├── architecture/        ← ADRs, modules, contracts
├── tasks/               ← Per-task folders with artifacts
│   └── task-feature-auth/
│       ├── plan.md
│       ├── spec.md
│       ├── rollback-plan.md
│       ├── architecture-review.md
│       ├── implementation-notes.md
│       ├── test-plan.md
│       ├── verification-report.md
│       ├── evidence-package.md
│       └── review.md
├── evidence/            ← Terminal output logs (auto-generated)
│   └── task-feature-auth/
│       ├── build-*.log
│       ├── types-*.log
│       ├── lint-*.log
│       ├── test-*.log
│       └── regression-*.log
├── state-machine.md     ← Task state definitions
├── task-template.md     ← Per-task checklist (copy this for new tasks)
├── GATE-CHECKLIST.md    ← All gate requirements
├── INTEGRATION-TEST.md  ← Example walkthrough (feature-auth)
├── QUICK-START.md       ← This file
└── READINESS.md         ← Phase 0 completion checklist
```

---

## Next Steps

1. **Read CLAUDE.md** → understand current status
2. **Check CLAUDE.md IN PROGRESS section** → is there a task already? If yes, see what state it's in
3. **If no active task:** Start new feature or bug fix following "I'm Starting a New Feature" section above
4. **If active task:** Find the appropriate agent section and continue

---

## One More Thing

This is ASES Phase 0 (bootstrap). The system enforces discipline:
- Every task goes through 6 gates
- Every gate requires evidence (not opinions)
- No skipping gates
- No fabricated evidence
- Independent review sessions (REVIEWER doesn't see BUILDER's code until the final review)

This prevents:
- Shipping untested code
- Claiming completion without evidence
- Overlooking bugs due to author bias

**Trust the gates. They work.**

---

*End of QUICK-START.md*
