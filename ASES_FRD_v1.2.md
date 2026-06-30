# FUNCTIONAL REQUIREMENTS DOCUMENT
# AI Software Engineering System (ASES)
# Version: 1.2 | Status: DRAFT | Owner: Solo Developer
# Changed from v1.0: Agents reduced 9→6, Evidence split into Producer/Interpreter,
#                    ADR system added, Task State Machine added, Rollback planning added
# Changed from v1.1: Token optimization (Part 17) — compact artifacts, context scoping,
#                    PLANNER+ARCHITECT fast path, tiered verification (iteration vs commit gate).
#                    Rigor is unchanged — only mechanics and verbosity are optimized.

---

## CRITICAL READING INSTRUCTIONS FOR CLAUDE

You are reading this document as an agent inside ASES. Before doing anything:
1. Identify which agent role you are currently playing
2. Read ONLY the sections relevant to your role
3. Never claim completion without producing the required artifact
4. Never proceed past a gate without explicit human approval
5. If you are uncertain, your only valid response is: STATUS: BLOCKED — reason: [explain]

This document is the source of truth. Your training data is not.

---

## PART 1: PROBLEM STATEMENT

### 1.1 The Core Problem

Claude CLI, when used without structure, exhibits three compounding failure modes:

**Failure Mode 1 — Isolated Implementation**
Claude implements each component in isolation. Function A works. Module B works. But nobody verified A and B work together with real data in real sequence. Integration is assumed, never verified.

**Failure Mode 2 — Fabricated Confidence**
When asked "does this work?", Claude pattern-matches to confidence rather than evidence. It says "yes, tested and working" because that is what a competent engineer sounds like. It has no actual evidence. It is pattern-matching to reassurance.

**Failure Mode 3 — No Honest Uncertainty**
Claude will not say "I don't know if this works end to end." It fills uncertainty with false confidence. This is structurally unavoidable without an external enforcement system.

### 1.2 The Consequence

The developer builds on top of unverified foundations. The product appears complete. When tested as a whole, it crashes. Claude then diagnoses fake fixes instead of admitting it never verified integration in the first place.

### 1.3 The Solution Principle

**Claude cannot mark anything complete without evidence it did not generate itself.**

Evidence must come from:
- Terminal output (compiler, linter, test runner)
- Captured log files with timestamps
- Actual command exit codes

Evidence never comes from:
- Claude's assessment of its own code
- Claude's memory of previous sessions
- Claude's confidence statements

---

## PART 2: SYSTEM OVERVIEW

### 2.1 What ASES Is

ASES is a protocol-based engineering operating system that runs inside Claude CLI. It transforms a single Claude session into a disciplined multi-agent engineering team by enforcing:

- Role separation (Builder ≠ Reviewer ≠ Tester)
- Artifact-driven handoffs (every role produces a document before the next role starts)
- Evidence-gated completion (no gate passes without terminal-produced evidence)
- Human approval at every checkpoint (nothing proceeds automatically)

### 2.2 What ASES Is Not

- ASES is not a software framework requiring installation
- ASES is not dependent on MCP servers or external APIs
- ASES is not a replacement for human judgment
- ASES is not a guarantee of bug-free code — it is a guarantee of honest status reporting

### 2.3 Runtime Environment

```
Runtime:         Claude CLI (no MCP servers)
Memory:          CLAUDE.md files on disk (no persistent session memory)
Evidence:        Terminal stdout/stderr captured to timestamped log files
Version Control: Git (mandatory, not optional)
Stacks:          TypeScript, Python (Ortho) | Kotlin, Java (Expense App)
Developer:       Solo (one human, all agent roles played by Claude in separate sessions)
```

### 2.4 Three Operating Situations

ASES must handle all three:

**Situation A — Building ASES itself (Bootstrap)**
Greenfield. Claude is unreliable during construction. Requires Phase 0 Bootstrap Protocol.

**Situation B — Continuing Ortho (Brownfield, ~30% complete)**
Existing code built without ASES guardrails. Unknown verified state. Requires Baseline Audit before new features are added.

**Situation C — New Features / Greenfield**
Standard ASES workflow applies. Both Ortho and Expense App after baseline established.

---

## PART 3: AGENT DEFINITIONS (v1.1 — Reduced from 9 to 5)

### Why 9 became 5

v1.0 had 9 separate agents. For a solo developer this created too much context switching and encouraged skipping steps. v1.1 consolidates into 5 roles by merging related responsibilities:

- TASK-DECOMPOSER merged into PLANNER (planning and decomposition are one thought process)
- REGRESSION-VALIDATOR merged into VERIFIER (all verification runs in one session)
- EVIDENCE-COLLECTOR merged into VERIFIER (collecting evidence is part of verification)
- TEST-DESIGNER stays separate — must never be the same session as BUILDER

The 5 agents are: **PLANNER · ARCHITECT · BUILDER · TEST-DESIGNER · VERIFIER · REVIEWER**

Wait — that is 6. REVIEWER stays separate because it must be an adversarial fresh session with zero BUILDER context. The consolidation brings us from 9 to 6, which is the right balance for daily use.

Each agent is a distinct Claude session with a distinct system prompt. No agent carries context from another agent's session. Handoffs happen through files on disk only.

---

### 3.1 Agent: PLANNER

**Purpose:** Translate a feature request into a verified plan and atomic task specifications ready for building. Never writes code.

**Absorbs from v1.0:** PLANNER + TASK-DECOMPOSER responsibilities.

**Reads:**
- `CLAUDE.md` (project working memory — read first, always)
- Feature request or bug report (provided by human)
- `.ases/architecture/decisions.md` (existing decisions)
- `.ases/architecture/modules.md` (module map)

**Writes:**
- `.ases/tasks/[task-id]/plan.md`
- `.ases/tasks/[task-id]/spec.md`
- `.ases/tasks/[task-id]/rollback-plan.md`
- Updated `CLAUDE.md`

**plan.md must include:**
- Feature summary (2-3 sentences)
- Atomic task breakdown (30-90 min each)
- Task dependency order
- Risk identification (what could go wrong)
- Acceptance criteria per task

**spec.md must include:**
- Objective (one sentence, specific)
- Files to create or modify (explicit paths)
- Files that must NOT be touched
- Input/output contracts (exact types/shapes)
- Acceptance criteria (testable, binary — pass or fail, no ambiguity)
- Dependencies on other tasks
- Required evidence to consider complete
- Change impact: affected modules, affected APIs, regression candidates

**rollback-plan.md must include:**
- Rollback trigger (what conditions require rollback)
- Rollback procedure (exact git commands)
- Affected components
- Verification after rollback (how to confirm rollback succeeded)
- Known rollback limitations

**Forbidden:**
- Writing any production code
- Making architecture decisions without flagging them for ARCHITECT
- Vague acceptance criteria ("should work correctly" is forbidden)
- Acceptance criteria that cannot produce terminal evidence
- Assuming previous session context not present in CLAUDE.md
- Marking tasks complete

**Gate:** Human reviews plan.md + spec.md + rollback-plan.md and explicitly approves all three before ARCHITECT or BUILDER is invoked.

---

### 3.2 Agent: ARCHITECT

**Purpose:** Validate architecture before implementation. Prevent structural mistakes before they are coded. Maintain the Architecture Decision Record.

**Reads:**
- `.ases/tasks/[task-id]/plan.md`
- `.ases/tasks/[task-id]/spec.md`
- `.ases/architecture/` (all files)
- `CLAUDE.md`

**Writes:**
- `.ases/tasks/[task-id]/architecture-review.md`
- `.ases/architecture/decisions.md` (append new decisions)
- `.ases/architecture/adrs/ADR-[NNN]-[title].md` (when ADR is required — see Part 5)
- Updated `.ases/architecture/modules.md` if boundaries change

**architecture-review.md must include:**
- Module boundary evaluation
- Dependency analysis (what depends on what)
- API contract definitions
- Data flow review
- Risk flags: security, scalability, extensibility
- ADR references (which ADRs apply, which new ones were created)
- Explicit verdict: APPROVED or REJECTED with specific reasons

**Forbidden:**
- Writing production code
- Approving without documented reasoning
- Proceeding if critical risks are unresolved
- Creating ADRs without filling all required fields (see Part 5)

**Gate:** Human reviews architecture-review.md. REJECTED returns to PLANNER with specific issues. APPROVED unblocks BUILDER.

---

### 3.3 Agent: BUILDER

**Purpose:** Implement exactly what the spec says. Nothing more. Nothing less.

**Reads:**
- `.ases/tasks/[task-id]/spec.md` (primary input — the only source of truth for scope)
- `.ases/tasks/[task-id]/architecture-review.md` (constraints only)
- `.ases/tasks/[task-id]/rollback-plan.md` (must read before writing a single line)
- `CLAUDE.md` (project context only)

**Writes:**
- Production code to paths specified in spec only
- `.ases/tasks/[task-id]/implementation-notes.md`

**implementation-notes.md must include:**
- What was built (specific, file by file)
- What was deliberately NOT built and why
- Any deviations from spec (each requires explicit justification)
- Complete list of files modified (exact paths)
- Commands the VERIFIER should run to check this work
- Honest assessment: what might break

**Forbidden:**
- Modifying files not listed in spec without documented justification
- Claiming the implementation is tested
- Claiming the implementation works
- Writing tests (TEST-DESIGNER's exclusive responsibility)
- Self-reviewing its own output
- Proceeding without reading rollback-plan.md first

**Gate:** Human reviews implementation-notes.md for scope violations before TEST-DESIGNER is invoked.

---

### 3.4 Agent: TEST-DESIGNER

**Purpose:** Design and write tests independently of the implementation. Adversarial by design. Must never be the same Claude session as the BUILDER session that wrote the code being tested.

**Reads:**
- `.ases/tasks/[task-id]/spec.md`
- `.ases/tasks/[task-id]/implementation-notes.md`
- The actual production code written by BUILDER

**Writes:**
- Test files to paths specified in spec
- `.ases/tasks/[task-id]/test-plan.md`

**test-plan.md must include:**
- Unit tests per acceptance criterion (one test minimum per criterion)
- Integration tests covering component boundaries
- Edge cases: empty inputs, nulls, boundary values, concurrent access
- Failure scenarios: what should fail gracefully and how
- Regression candidates: existing tests likely affected by this change

**Forbidden:**
- Marking tests as passing before they are run
- Writing only happy path tests
- Skipping edge cases because they seem unlikely
- Approving the implementation
- Sharing session context with the BUILDER that wrote the code

**Gate:** Human reviews test-plan.md before VERIFIER runs.

---

### 3.5 Agent: VERIFIER

**Purpose:** Produce evidence and interpret it honestly. Two distinct responsibilities in one session, but with a hard rule: evidence is produced first, interpretation second. Claude must never claim to have run commands it did not run.

**Absorbs from v1.0:** VERIFIER + REGRESSION-VALIDATOR + EVIDENCE-COLLECTOR responsibilities.

**This agent has two modes:**

#### Mode A — Evidence Production
Execute actual terminal commands. Capture all output to timestamped log files. Do not interpret yet.

```bash
# TypeScript/Ortho
tsc --noEmit 2>&1 | tee .ases/evidence/$TASK_ID/build-$(date +%s).log
echo "EXIT:$?" >> .ases/evidence/$TASK_ID/build-$(date +%s).log
eslint . 2>&1 | tee .ases/evidence/$TASK_ID/lint-$(date +%s).log
echo "EXIT:$?" >> .ases/evidence/$TASK_ID/lint-$(date +%s).log
jest --coverage 2>&1 | tee .ases/evidence/$TASK_ID/test-$(date +%s).log
echo "EXIT:$?" >> .ases/evidence/$TASK_ID/test-$(date +%s).log
# Full regression suite
jest --testPathPattern=".*" 2>&1 | tee .ases/evidence/$TASK_ID/regression-$(date +%s).log

# Python/Ortho
ruff check . 2>&1 | tee .ases/evidence/$TASK_ID/lint-$(date +%s).log
mypy . --strict 2>&1 | tee .ases/evidence/$TASK_ID/types-$(date +%s).log
pytest --tb=short --cov=. 2>&1 | tee .ases/evidence/$TASK_ID/test-$(date +%s).log
pytest 2>&1 | tee .ases/evidence/$TASK_ID/regression-$(date +%s).log

# Kotlin/Java Expense App
./gradlew ktlintCheck 2>&1 | tee .ases/evidence/$TASK_ID/lint-$(date +%s).log
./gradlew build 2>&1 | tee .ases/evidence/$TASK_ID/build-$(date +%s).log
./gradlew test 2>&1 | tee .ases/evidence/$TASK_ID/test-$(date +%s).log
```

**Evidence production rules:**
- Every command output goes to a file. Nothing is held in memory only.
- Exit code is appended to every log file immediately after the command.
- If a command cannot be run (missing tool, wrong environment), write that fact to the log. Do not skip it silently.
- Claude must never claim it ran a command if it did not. If Claude cannot execute commands in this session, write: `EVIDENCE-SOURCE: HUMAN-TERMINAL` and wait for the human to provide log files.

#### Mode B — Evidence Interpretation
Read the log files produced in Mode A. Never interpret from memory.

**Reads (in this order, no skipping):**
- Every log file in `.ases/evidence/[task-id]/`
- `.ases/tasks/[task-id]/spec.md` (to compare expected vs actual)
- `.ases/tasks/[task-id]/test-plan.md` (to verify test coverage)

**Writes:**
- `.ases/tasks/[task-id]/verification-report.md`
- `.ases/tasks/[task-id]/evidence-package.md`

**verification-report.md structure:**
```
TASK:           [task-id]
TIMESTAMP:      [actual datetime]
EVIDENCE-SOURCE: CLAUDE-CLI | HUMAN-TERMINAL | CI-CD

BUILD:          PASS | FAIL | NOT-RUN — [log file reference]
LINT:           PASS | FAIL | NOT-RUN — [log file reference]
TYPE-CHECK:     PASS | FAIL | NOT-RUN — [log file reference]
UNIT-TESTS:     PASS | FAIL | NOT-RUN — [X passed, Y failed] — [log file reference]
COVERAGE:       [percentage] | NOT-MEASURED
REGRESSION:     PASS | FAIL | NOT-RUN — [X new failures] — [log file reference]
ANDROID-UI:     NOT-APPLICABLE (requires emulator) | MANUAL-REQUIRED

FAILURES (copy exact text from log files — never summarize):
[paste actual error lines here]

REGRESSION-DELTA:
  Tests before: [N]
  Tests after:  [N]
  Newly failing: [names]
  Newly passing: [names]

STATUS: VERIFIED | UNVERIFIED | BLOCKED | FAILED
CONFIDENCE: EVIDENCE-BACKED | PARTIAL | LOW
```

**evidence-package.md structure:**
```
TASK:           [task-id]
DESCRIPTION:    [what was built]
COMPLETED:      [datetime]

GATES PASSED:
✓/✗ Plan approved by human           [datetime or MISSING]
✓/✗ Architecture approved by human   [datetime or MISSING]
✓/✗ Spec approved by human           [datetime or MISSING]
✓/✗ Rollback plan exists             [file path or MISSING]
✓/✗ Implementation scoped correctly  [implementation-notes.md confirms]
✓/✗ Tests written independently      [test-plan.md exists]
✓/✗ Build PASSED                     [log file]
✓/✗ Lint PASSED                      [log file]
✓/✗ Type check PASSED                [log file]
✓/✗ Unit tests PASSED                [X/Y, log file]
✓/✗ Regression PASSED                [log file]

KNOWN LIMITATIONS:
[honest list — "none" requires explicit written justification]

READY FOR REVIEW: YES | NO — [reason if NO]
```

**Forbidden:**
- Reporting PASS without a log file reference
- Summarizing errors instead of quoting them from the log
- Marking STATUS: VERIFIED if any check failed
- Interpreting failures optimistically
- Claiming to have run commands that were not run
- Writing "none" under Known Limitations without justification

**Gate:** Human reads verification-report.md AND opens at least one log file directly to spot-check. Not Claude's summary. The actual file.

---

### 3.6 Agent: REVIEWER

**Purpose:** Adversarial code review from a fresh perspective. Actively seeks failures. Must be a completely fresh Claude session with no prior context from the BUILDER session.

**Reads:**
- `.ases/tasks/[task-id]/spec.md`
- `.ases/tasks/[task-id]/verification-report.md`
- `.ases/tasks/[task-id]/evidence-package.md`
- `.ases/evidence/[task-id]/` (actual log files — not summaries)
- The actual production code

**The REVIEWER asks itself (must address each question explicitly):**
1. What would make this break in production?
2. What did BUILDER not test?
3. What assumption is this code making that has not been verified?
4. What happens when dependencies fail?
5. What is the security surface of this change?
6. Does this violate any ADR or architecture decision?
7. Is the evidence complete or were gates skipped?

**Writes:**
- `.ases/tasks/[task-id]/review.md`

**review.md must include:**
- Verdict: APPROVED or CHANGES REQUIRED (no other options)
- If CHANGES REQUIRED: specific issues with file name and line number
- Security assessment (cannot be skipped)
- Architecture compliance (references specific ADRs if relevant)
- Evidence completeness assessment
- Confidence: EVIDENCE-BACKED | PARTIAL | LOW

**Forbidden:**
- Approving without reading the actual evidence log files
- Rubber-stamping because VERIFIER passed
- Vague feedback ("consider improving error handling" without specifics)
- Approving if verification-report STATUS is UNVERIFIED or FAILED
- Any knowledge of or reference to the BUILDER session context

**Gate:** Human reviews review.md. CHANGES REQUIRED returns to BUILDER with specific file/line issues. APPROVED unblocks commit.

---

## PART 4: TASK STATE MACHINE

Every task has an explicit state. State transitions require specific artifacts and human approval. No task can be in an ambiguous state.

### 4.1 States

```
DRAFT              — Task identified but not yet planned
PLANNED            — plan.md + spec.md + rollback-plan.md exist, awaiting human approval
ARCH-REVIEW        — Architecture review in progress or awaiting human approval
READY-TO-BUILD     — All pre-build gates approved, BUILDER can start
IMPLEMENTED        — BUILDER session complete, implementation-notes.md exists
TESTS-WRITTEN      — TEST-DESIGNER session complete, test-plan.md exists
VERIFICATION       — VERIFIER running or awaiting evidence
VERIFIED           — verification-report STATUS: VERIFIED
REVIEW             — REVIEWER session in progress
APPROVED           — review.md verdict: APPROVED
COMMITTED          — Git commit exists with evidence reference
BLOCKED            — Cannot proceed, reason documented
CHANGES-REQUIRED   — REVIEWER returned issues, awaiting BUILDER fix
FAILED             — Verification produced failures, awaiting decision
ROLLED-BACK        — Rollback executed, rollback verified
```

### 4.2 Valid Forward Transitions

| From | To | Required Artifact | Required Approval |
|---|---|---|---|
| DRAFT | PLANNED | plan.md + spec.md + rollback-plan.md | Human |
| PLANNED | ARCH-REVIEW | architecture-review.md started | Human (triggers ARCHITECT) |
| PLANNED | READY-TO-BUILD | Architecture waived (simple tasks only) | Human explicit waiver |
| ARCH-REVIEW | READY-TO-BUILD | architecture-review.md: APPROVED | Human |
| READY-TO-BUILD | IMPLEMENTED | implementation-notes.md | Human (scope check) |
| IMPLEMENTED | TESTS-WRITTEN | test-plan.md | Human |
| TESTS-WRITTEN | VERIFICATION | VERIFIER session started | — |
| VERIFICATION | VERIFIED | verification-report: VERIFIED | Log files (not Claude) |
| VERIFICATION | FAILED | verification-report: FAILED | Log files (not Claude) |
| VERIFIED | REVIEW | REVIEWER session started | — |
| REVIEW | APPROVED | review.md: APPROVED | Human |
| APPROVED | COMMITTED | Git commit with evidence | Human (runs git) |

### 4.3 Valid Rollback Transitions

| From | To | Trigger | Required Action |
|---|---|---|---|
| CHANGES-REQUIRED | IMPLEMENTED | REVIEWER returned specific issues | BUILDER fixes in new session |
| FAILED | READY-TO-BUILD | Human decides to fix, not abandon | BUILDER addresses failures |
| FAILED | ROLLED-BACK | Human decides to revert | Execute rollback-plan.md |
| BLOCKED | PLANNED | Blocker resolved | Human re-approves plan |
| ANY | BLOCKED | Unresolvable dependency or risk | Document reason in CLAUDE.md |

### 4.4 State in CLAUDE.md

Every task listed in CLAUDE.md must show its current state:

```
## IN PROGRESS
task-007 | add expense categories | STATE: VERIFIED | waiting for REVIEWER session
task-008 | fix auth token refresh | STATE: READY-TO-BUILD | BUILDER not yet started
```

---

## PART 5: ARCHITECTURE DECISION RECORDS (ADR)

### 5.1 What an ADR Is

An ADR permanently records a significant architecture decision. Architecture reviews evaluate a plan. ADRs record what was decided and why. They are append-only — never deleted, never edited after ACCEPTED status.

### 5.2 When ADR Creation Is Mandatory

Create an ADR when any of these are true:
- A new module, service, or layer is introduced
- A dependency is added to the project
- An API contract is defined or changed
- A database schema design is decided
- A security approach is chosen
- A decision reverses or overrides a previous decision
- A decision will be hard or expensive to change later

### 5.3 When ADR Is Optional

ADR is optional for:
- Bug fixes that don't change design
- Refactoring within existing module boundaries
- Adding a feature that fits cleanly into existing patterns

### 5.4 ADR File Location and Naming

```
.ases/architecture/adrs/
  ADR-001-use-typescript-for-ortho-core.md
  ADR-002-sqlite-for-local-expense-storage.md
  ADR-003-repository-pattern-for-data-layer.md
```

Format: `ADR-[NNN]-[kebab-case-title].md`
Numbers are sequential and never reused.

### 5.5 ADR Template

```markdown
# ADR-[NNN]: [Title]
Status: DRAFT | PROPOSED | ACCEPTED | SUPERSEDED BY ADR-[NNN]
Date: [YYYY-MM-DD]
Author: [agent role that created it]
Approved by: Human on [date]

## Context
[What situation led to this decision needing to be made?]

## Problem Statement
[What specific problem does this decision solve?]

## Alternatives Considered
[List every alternative evaluated, not just the winner]
- Option A: [description] — rejected because [reason]
- Option B: [description] — rejected because [reason]
- Option C (chosen): [description]

## Decision
[State the decision clearly in one paragraph]

## Rationale
[Why this option over the alternatives? Be specific.]

## Consequences
Positive:
- [what becomes easier]
Negative:
- [what becomes harder or constrained]
Neutral:
- [what changes but is neither good nor bad]

## Future Considerations
[What might cause this decision to be revisited?]

## Related Tasks
- task-[id]: [description]

## Related ADRs
- ADR-[NNN]: [title] — [relationship]
```

### 5.6 ADR Lifecycle

```
DRAFT      — ARCHITECT is writing it
PROPOSED   — Written, awaiting human approval
ACCEPTED   — Human approved, locked (no editing content)
SUPERSEDED — A newer ADR overrides this one (note the new ADR number)
```

Once ACCEPTED, the only valid edit is changing status to SUPERSEDED and adding the superseding ADR reference.

### 5.7 ADR Index

`.ases/architecture/adrs/INDEX.md` — maintained by ARCHITECT, lists all ADRs with status and one-line summary. Updated whenever a new ADR is created or status changes.

---

## PART 6: EVIDENCE SYSTEM

### 6.1 Evidence Principles

Evidence is valid only if:
1. Produced by a tool (compiler, linter, test runner), not by Claude
2. Captured to a timestamped file on disk
3. The file exists and can be read independently of Claude
4. The exit code is recorded alongside the output
5. The file content matches Claude's reported status

Evidence is invalid if:
1. Claude summarizes it from memory without a file reference
2. The log file does not exist
3. The log file shows failures but Claude reports success
4. The timestamp is implausible

### 6.2 Evidence Sources (in order of trust)

```
LEVEL 1 — STRONGEST
  CI/CD system output (GitHub Actions, etc.)
  Reason: Runs in isolated environment, not influenced by local state

LEVEL 2 — STRONG
  Human-run terminal commands, output pasted or saved to log files
  Reason: Human observed the actual execution

LEVEL 3 — ACCEPTABLE
  Claude CLI executing commands directly, output captured to files
  Reason: Claude ran it but cannot verify its own honesty — file is the check

LEVEL 4 — NOT ACCEPTED AS GATE EVIDENCE
  Claude's assessment of its own code
  Claude's memory of previous results
  Claude's confidence statements
  Paraphrased or summarized output
```

### 6.3 Evidence Source Declaration

Every verification-report.md must declare its evidence source:

```
EVIDENCE-SOURCE: CLAUDE-CLI | HUMAN-TERMINAL | CI-CD | MIXED
```

If MIXED, list which checks came from which source.

### 6.4 Evidence Cannot Be Faked By Claude

The core architectural guarantee: **Claude interprets evidence files, it does not write them.**

Log files are written by tools (tsc, pytest, gradle). Claude reads them. If Claude writes a log file manually, that is fabrication and the gate is BLOCKED. The human must spot-check log files directly to enforce this.

---

## PART 7: WORKFLOW ENGINE

### 7.1 Standard Feature Workflow

```
HUMAN provides feature request
    ↓
PLANNER session
  produces: plan.md + spec.md + rollback-plan.md
  task state: DRAFT → PLANNED
    ↓
[GATE 1] Human approves all three documents
    ↓ APPROVED
ARCHITECT session (skip only with explicit human waiver for simple tasks)
  produces: architecture-review.md, ADRs if required
  task state: PLANNED → ARCH-REVIEW → READY-TO-BUILD
    ↓
[GATE 2] Human approves architecture-review.md
    ↓ APPROVED
BUILDER session
  reads: spec.md + rollback-plan.md (mandatory)
  produces: code + implementation-notes.md
  task state: READY-TO-BUILD → IMPLEMENTED
    ↓
[GATE 3] Human reviews implementation-notes.md for scope violations
    ↓ NO VIOLATIONS
TEST-DESIGNER session (must be fresh — no BUILDER context)
  produces: tests + test-plan.md
  task state: IMPLEMENTED → TESTS-WRITTEN
    ↓
VERIFIER session
  Mode A: runs commands, captures logs
  Mode B: reads logs, produces verification-report.md + evidence-package.md
  task state: TESTS-WRITTEN → VERIFICATION → VERIFIED or FAILED
    ↓
[GATE 4] Human reads verification-report.md AND spot-checks log files
    ↓ STATUS: VERIFIED
REVIEWER session (fresh — zero BUILDER context)
  produces: review.md
  task state: VERIFIED → REVIEW → APPROVED or CHANGES-REQUIRED
    ↓
[GATE 5] Human reviews review.md
    ↓ APPROVED
Human runs git commit with evidence reference
  task state: APPROVED → COMMITTED
    ↓
CLAUDE.md updated: task moved to COMPLETED
```

### 7.2 Bug Fix Workflow

Skips ARCHITECT unless the fix touches architecture. All other gates apply.

```
HUMAN describes bug with exact reproduction steps
    ↓
PLANNER session
  produces: plan.md (root cause analysis) + spec.md (fix scope) + rollback-plan.md
    ↓
[GATE 1] Human approves fix approach
    ↓
BUILDER session → TEST-DESIGNER session → VERIFIER session → REVIEWER session
    ↓
Human commits
```

### 7.3 Baseline Audit Workflow (Brownfield — Ortho)

Run once before ASES takes over the existing Ortho codebase. No new features until this is done.

```
VERIFIER session (Mode A only — just run and capture, no interpretation yet)
  runs full verification suite on existing code
  captures all output to .ases/baseline/
    ↓
VERIFIER session (Mode B only — interpret the captured logs)
  produces .ases/baseline/verification-report.md
    ↓
REVIEWER session (adversarial review of existing codebase)
  produces .ases/baseline/audit-report.md
    ↓
[GATE] Human reviews both reports
    ↓
Human decision: fix baseline issues first OR document as known debt
  either way: .ases/baseline/baseline-snapshot.md is produced
    ↓
ASES standard workflows apply from this point forward
All new work starts with PLANNER
```

### 7.4 Bootstrap Protocol (Phase 0 — Building ASES Itself)

Minimal protocol for use while ASES is being constructed. Full ASES cannot govern its own construction.

**Five rules only:**

1. Every session starts by reading CLAUDE.md if it exists
2. Every session ends by updating CLAUDE.md with what changed and current task state
3. No session claims a component is "done" — only "implemented, unverified" or "verified: [evidence file]"
4. After every implementation session, run the appropriate verification command, capture output to a file, read the file — do not summarize from memory
5. Git commit after every verified unit. Commit message includes evidence file path.

---

## PART 8: FOLDER STRUCTURE

```
[project-root]/
├── CLAUDE.md                          ← Project working memory (read first, always)
│
├── .ases/
│   ├── agents/                        ← Agent system prompts (one file per agent)
│   │   ├── planner.md
│   │   ├── architect.md
│   │   ├── builder.md
│   │   ├── test-designer.md
│   │   ├── verifier.md
│   │   └── reviewer.md
│   │
│   ├── workflows/                     ← Workflow definitions
│   │   ├── feature.md
│   │   ├── bugfix.md
│   │   ├── baseline-audit.md
│   │   └── bootstrap.md
│   │
│   ├── templates/                     ← Output templates (fill these in per task)
│   │   ├── plan.md
│   │   ├── spec.md
│   │   ├── rollback-plan.md
│   │   ├── architecture-review.md
│   │   ├── implementation-notes.md
│   │   ├── test-plan.md
│   │   ├── verification-report.md
│   │   ├── review.md
│   │   ├── evidence-package.md
│   │   └── adr.md
│   │
│   ├── architecture/
│   │   ├── decisions.md              ← Append-only log of all decisions (summary)
│   │   ├── modules.md                ← Module map, updated by ARCHITECT
│   │   ├── contracts.md              ← API/interface contracts
│   │   └── adrs/                     ← Full ADR files
│   │       ├── INDEX.md              ← ADR index (status + one-liner per ADR)
│   │       └── ADR-001-[title].md
│   │
│   ├── tasks/                         ← One folder per task
│   │   └── [task-id]/
│   │       ├── plan.md
│   │       ├── spec.md
│   │       ├── rollback-plan.md
│   │       ├── architecture-review.md  (may not exist for simple tasks)
│   │       ├── implementation-notes.md
│   │       ├── test-plan.md
│   │       ├── verification-report.md
│   │       ├── review.md
│   │       └── evidence-package.md
│   │
│   ├── evidence/                      ← Terminal output logs (never edited manually)
│   │   ├── baseline/                 ← Baseline audit logs
│   │   └── [task-id]/
│   │       ├── build-[timestamp].log
│   │       ├── lint-[timestamp].log
│   │       ├── types-[timestamp].log
│   │       ├── test-[timestamp].log
│   │       └── regression-[timestamp].log
│   │
│   ├── baseline/                      ← Brownfield baseline (Ortho)
│   │   ├── verification-report.md
│   │   ├── audit-report.md
│   │   └── baseline-snapshot.md
│   │
│   └── commands/                      ← Verification shell scripts
│       ├── verify-ts.sh
│       ├── verify-python.sh
│       ├── verify-android.sh
│       └── capture-evidence.sh
```

---

## PART 9: CLAUDE.md SPECIFICATION

CLAUDE.md is the only persistent memory across sessions. Every agent reads it first. Every agent updates it last. Never delete content — only append or update.

### 9.1 CLAUDE.md Structure

```markdown
# CLAUDE.md — [Project Name]
Last updated: [datetime] by [agent-role]

## PROJECT IDENTITY
[Name, purpose — 3 sentences max]

## STACK
[Languages, frameworks, tools — specific versions]

## CURRENT STATUS
Phase: BOOTSTRAP | BASELINE-AUDIT | ACTIVE-DEVELOPMENT
Active task: [task-id] | STATE: [state] | NONE
Last verified commit: [git hash]
Last verified datetime: [datetime]

## ARCHITECTURE DECISIONS
[Append-only. Format: DATE | DECISION | REASON | ADR reference]

## COMPLETED TASKS
[task-id] | [description] | [evidence-package path] | [git hash] | [date]

## IN PROGRESS
[task-id] | [description] | STATE: [state] | [current agent or waiting for what]

## BLOCKED
[task-id] | [description] | BLOCKED: [exact reason] | [date blocked]

## KNOWN ISSUES
[Honest list. "None" requires explicit confirmation in writing.]

## FORBIDDEN ACTIONS
[Project-specific rules Claude must never violate — add as discovered]

## VERIFICATION COMMANDS
[Exact commands for this project — no placeholders]
```

---

## PART 10: CHECKPOINT SYSTEM

| Checkpoint | Required Artifact | Required Evidence | Approver |
|---|---|---|---|
| PLAN-APPROVED | plan.md + spec.md + rollback-plan.md | Human reads all three | Human |
| ARCH-APPROVED | architecture-review.md | Human reads it | Human |
| SCOPE-CLEAN | implementation-notes.md | Human checks no drift | Human |
| BUILD-PASSED | build log | tool exit 0 | Log file |
| LINT-PASSED | lint log | tool exit 0 | Log file |
| TYPES-PASSED | types log | tool exit 0 | Log file |
| TESTS-PASSED | test log | 0 failures | Log file |
| REGRESSION-CLEAN | regression log | 0 new failures | Log file |
| REVIEW-APPROVED | review.md | verdict: APPROVED | Human |
| EVIDENCE-COMPLETE | evidence-package.md | all gates ✓ | Human |
| COMMITTED | git log | commit hash exists | Git |

---

## PART 11: DEFINITION OF DONE

A task is DONE only when ALL of the following are true. Not most. All.

```
□ plan.md exists and was human-approved
□ spec.md exists and was human-approved
□ rollback-plan.md exists (was read by BUILDER before coding)
□ architecture-review.md exists OR architecture waiver explicitly documented
□ ADRs created for any significant decisions (see Part 5)
□ Implementation matches spec scope — implementation-notes.md confirms
□ Tests written by TEST-DESIGNER in a separate session from BUILDER
□ Build log exists, exit code 0
□ Lint log exists, exit code 0
□ Type check log exists, exit code 0
□ Test log exists, 0 failures
□ Regression log exists, 0 new failures
□ verification-report.md STATUS: VERIFIED
□ review.md verdict: APPROVED
□ evidence-package.md READY-FOR-REVIEW: YES
□ CLAUDE.md updated: task in COMPLETED list with git hash
□ Git commit exists referencing evidence-package
```

If any item is unchecked, the only valid status is: **INCOMPLETE**

---

## PART 12: FORBIDDEN PHRASES

Claude must never output these as status claims without an evidence file reference:

- "Implementation complete"
- "Successfully implemented"
- "Fully tested"
- "Everything works"
- "Production ready"
- "All tests passing"
- "No issues found"
- "Looks good" (as a review verdict)
- "Should work" (as a verification claim)
- "I ran the tests and they passed" (without log file path)

If Claude produces any of these without a corresponding log file reference, the statement is automatically INVALID and the gate is BLOCKED.

---

## PART 13: GIT WORKFLOW

### 13.1 Branch Strategy

```
main          ← verified, evidence-backed commits only
  └── develop ← integration branch
        └── ases/[task-id]-[short-description] ← one branch per task
```

### 13.2 Commit Convention

```
[task-id]: [what changed — specific]

Evidence: .ases/evidence/[task-id]/
Gates: BUILD ✓ LINT ✓ TYPES ✓ TESTS ✓ REGRESSION ✓ REVIEW ✓
ADRs: ADR-[NNN] (if applicable)
Confidence: EVIDENCE-BACKED
```

### 13.3 Rollback

If regression is detected post-merge, execute rollback-plan.md for that task:
```bash
git revert [commit-hash]   # never git reset on any branch with history
# Create new task for the revert: task-[N]-revert-[description]
# Run Baseline Audit workflow after revert to confirm clean state
```

---

## PART 14: STACK-SPECIFIC VERIFICATION

### 14.1 Ortho (TypeScript)

```bash
tsc --noEmit                          # Type checking — must exit 0
eslint . --ext .ts,.tsx               # Linting — must exit 0
jest --coverage --ci                  # Tests — 0 failures, ≥80% coverage
jest --testPathPattern=".*"           # Regression — compare to baseline count
```

### 14.2 Ortho (Python)

```bash
ruff check .                          # Linting — must exit 0
mypy . --strict                       # Type checking — must exit 0
pytest --tb=short --cov=. --cov-report=term-missing   # Tests + coverage ≥80%
pytest                                # Regression — compare to baseline count
```

### 14.3 Expense App (Kotlin/Java)

```bash
./gradlew ktlintCheck                 # Linting — must exit 0
./gradlew build                       # Compilation — must exit 0
./gradlew test                        # Unit tests — 0 failures
```

**Android UI gap:** UI and end-to-end tests require an emulator. These cannot be captured as terminal evidence in CLI workflow. Every verification-report.md for the Expense App must include:
```
ANDROID-UI: MANUAL-REQUIRED — emulator tests not run in this session
```
This is not a failure. It is honest documentation of a real limitation.

---

## PART 15: KNOWN SYSTEM LIMITATIONS

These are honest limitations. Do not hide them.

1. **Solo developer paradox:** One human plays all roles. Structural separation is enforced through mandatory session separation and adversarial prompts, but human fatigue can still cause rubber-stamping. No technical solution fully eliminates this.

2. **Android UI verification gap:** Gradle covers unit/integration. UI tests need an emulator. Document as MANUAL-REQUIRED every time.

3. **No session memory:** CLAUDE.md is the only bridge between sessions. If it becomes stale, agents operate with wrong context. Must be updated at the end of every session without exception.

4. **Bootstrap paradox:** ASES is built using Phase 0 which is less rigorous than full ASES. Post-build, a baseline audit of ASES itself is required.

5. **Evidence cherry-picking:** A human could run commands until they pass and save only passing logs. This is a process integrity issue, not a technical one. The protocol assumes good faith.

6. **Claude CLI command execution uncertainty:** Claude may not always be able to execute shell commands depending on environment. VERIFIER must declare EVIDENCE-SOURCE honestly and never fabricate command output.

---

## PART 16: IMPLEMENTATION PHASES

### Phase 0 — Bootstrap (Build ASES)
**Goal:** Build ASES itself using the Bootstrap Protocol
**Deliverable:** Complete .ases/ repository with all agents, workflows, templates, commands
**Success criteria:** ASES can run its own Baseline Audit on itself

### Phase 1 — Ortho Baseline Audit
**Goal:** Establish verified current state of existing Ortho codebase (~30% built)
**Deliverable:** .ases/baseline/baseline-snapshot.md with honest assessment
**Success criteria:** Known issues documented, verified working components identified, known debt explicitly accepted or queued for fix

### Phase 2 — Ortho Active Development
**Goal:** Continue Ortho under full ASES governance
**Deliverable:** Each feature with complete evidence package and ADRs for major decisions
**Success criteria:** No unverified claims in git history from this point forward

### Phase 3 — Expense App
**Goal:** Build expense tracking app under ASES governance from the start
**Deliverable:** Each feature with complete evidence package
**Success criteria:** Same as Phase 2 plus Android verification gap documented consistently

### Phase 4 — Ortho Absorbs ASES
**Goal:** ASES workflows become executable inside Ortho as an orchestration engine
**Deliverable:** ASES prompts, templates, workflows importable by Ortho programmatically
**Success criteria:** A workflow can be triggered by Ortho and produce the same artifacts as manual execution — implementation-agnostic, works with any LLM backend

---

## PART 17: TOKEN OPTIMIZATION (v1.2 addition)

ASES v1.1 enforces rigor correctly but is expensive in practice — every session re-reads full context and produces verbose artifacts. v1.2 cuts token usage through mechanics, not rigor. Every gate, every evidence requirement, every forbidden phrase from v1.1 still applies in full. Nothing here weakens enforcement.

### 17.1 Principle

**Optimize what gets re-read and how much gets written. Never optimize what gets checked.**

### 17.2 Session Consolidation — PLANNER+ARCHITECT Fast Path

For tasks where ARCHITECT would clearly approve with no changes (no new module, no new dependency, no API change, fits existing patterns), PLANNER produces a `architecture-impact: NONE` flag in spec.md. If the human agrees, ARCHITECT is skipped as a separate session — PLANNER's session directly writes a one-line `architecture-review.md: WAIVED — no structural impact, see spec.md`.

If `architecture-impact: NONE` is wrong (BUILDER discovers it does touch architecture), the task moves to BLOCKED and a real ARCHITECT session is required. This is a fast path, not a rule weakening — mandatory-ADR triggers from Part 5.2 still force a full ARCHITECT session regardless of this flag.

### 17.3 Compact Artifact Format

All templates in `.ases/templates/` move from prose markdown to dense key-value blocks. Same required fields as v1.1, same forbidden-phrase rules, same evidence-reference requirements — just no narrative prose padding.

Example — spec.md, v1.1 style vs v1.2 style:

```
v1.1 (verbose):
## Objective
This task involves adding a new repository method that will allow
the application to fetch expense categories from local storage...

v1.2 (compact):
task: task-007
objective: Add ExpenseCategoryRepository.getAll() reading from SQLite
files_touch: [data/ExpenseCategoryRepository.kt]
files_forbid: [*]  # nothing else
contract_in: none
contract_out: List<ExpenseCategory>
acceptance:
  - getAll() returns empty list on empty table — evidence: unit test
  - getAll() returns all rows ordered by name — evidence: unit test
arch_impact: NONE
risk: LOW
```

This applies to every template: plan, spec, rollback-plan, implementation-notes, verification-report, evidence-package, review. Headers are single words. Lists are flat. No restating context the reader already has from the file path.

### 17.4 Context Scoping — Read Slices, Not Whole Files

As `.ases/architecture/decisions.md` and ADRs grow, agents must not re-read the entire file every session.

Rule: PLANNER and ARCHITECT read only `.ases/architecture/modules.md` (kept short, current-state-only) plus the ADR Index (one-line-per-ADR), not full ADR bodies. Full ADR text is opened only when the Index flags it as relevant to the current task.

CLAUDE.md stays small by design — `COMPLETED TASKS` entries are one line each (already true in v1.1). If CLAUDE.md exceeds ~150 lines, move completed-task history older than the last 10 tasks to `.ases/architecture/history.md` and reference it, not inline it.

### 17.5 Scoped Verification During Iteration vs Full Gate at Commit

Two verification tiers, both already-mandatory checks, just run at different times:

**Tier 1 — Iteration loop (BUILDER ↔ VERIFIER, before REVIEWER):**
Run build + lint + types + unit tests for files in `files_touch` and their direct importers only. Fast feedback while fixing issues.

**Tier 2 — Commit Gate (mandatory, unchanged from v1.1):**
Full build, full lint, full type-check, full test suite, full regression suite — exactly as Part 14 specifies. This tier cannot be skipped or scoped down. It is the actual gate. Tier 1 just avoids re-running the full gate five times while iterating on the same fix.

verification-report.md must declare which tier produced which result:
```
tier: ITERATION | COMMIT-GATE
```
Only a COMMIT-GATE tier result can move a task to VERIFIED.

### 17.6 What This Does NOT Change

- All 6 agent roles and their session-isolation rules (Part 3) — unchanged
- All required artifacts — unchanged, just denser format
- Forbidden phrases (Part 12) — unchanged
- Definition of Done (Part 11) — unchanged, every checkbox still required
- Evidence rules (Part 6) — unchanged, logs still tool-produced, still file-based
- Full regression before commit — unchanged, still mandatory
- ADR mandatory triggers (Part 5.2) — unchanged, still force a real ARCHITECT session

### 17.7 Expected Impact

Rough estimate, not measured yet: compact templates cut artifact tokens by roughly half. Context scoping cuts re-read tokens as the project grows. The PLANNER+ARCHITECT fast path removes one full session for the majority of small tasks. Full rigor is preserved because the Commit Gate (17.5) and Definition of Done (Part 11) are untouched — optimization only touches the iteration loop and document formatting.

---

## APPENDIX A: QUICK REFERENCE — WHICH AGENT AM I?

Your session's opening instruction tells you your role. If it does not, ask the human before doing anything.

| Agent | First Action | Primary Output |
|---|---|---|
| PLANNER | Read CLAUDE.md + feature request | plan.md + spec.md + rollback-plan.md |
| ARCHITECT | Read plan.md + spec.md + .ases/architecture/ | architecture-review.md + ADRs |
| BUILDER | Read spec.md + rollback-plan.md | code + implementation-notes.md |
| TEST-DESIGNER | Read spec.md + code (never BUILDER's session) | tests + test-plan.md |
| VERIFIER | Run commands → read logs → report | verification-report.md + evidence-package.md |
| REVIEWER | Read spec + evidence + code (fresh session) | review.md |

---

## APPENDIX B: STATUS VOCABULARY

Only these statuses are valid. No others.

```
VERIFIED          — Evidence exists, gates passed, log files confirm
UNVERIFIED        — No evidence produced yet
BLOCKED           — Cannot proceed — reason must be stated explicitly
IN-PROGRESS       — Currently being worked on
APPROVED          — Human has explicitly approved
CHANGES-REQUIRED  — Reviewer returned specific issues (file + line)
INCOMPLETE        — Definition of Done not fully satisfied
FAILED            — Verification produced failures — log file referenced
ROLLED-BACK       — Rollback executed and verified
NOT-APPLICABLE    — Gate does not apply — reason must be stated
MANUAL-REQUIRED   — Cannot be verified automatically — human must verify
```

---

## APPENDIX C: ADR INDEX TEMPLATE

```markdown
# ADR Index
Last updated: [datetime]

| ADR | Title | Status | Date | Summary |
|---|---|---|---|---|
| ADR-001 | [title] | ACCEPTED | [date] | [one sentence] |
```

---

*End of FRD v1.2*
*This document is the source of truth for ASES.*
*When in doubt, consult this document, not your training data.*
*Changes from v1.0→v1.1: Agents 9→6, Evidence Producer/Interpreter split, ADR system (Part 5), Task State Machine (Part 4), Rollback planning added to PLANNER output.*
*Changes from v1.1→v1.2: Token optimization (Part 17) — same rigor, leaner mechanics.*
