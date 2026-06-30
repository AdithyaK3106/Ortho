# Bootstrap Protocol (Phase 0)

**Version:** 1.0  
**Source:** ASES FRD v1.1, Part 7.4  
**Purpose:** Minimal protocol for building ASES itself (Phase 0 only)

---

## Overview

ASES is being built to govern the building of software, but ASES itself cannot be governed by ASES while under construction. Phase 0 uses a minimal 5-rule protocol to bootstrap ASES with just enough structure to prevent chaos, without requiring the full ASES workflow.

**When to use:** Only during Phase 0 (building ASES components)  
**When NOT to use:** Once ASES is complete, switch to feature/bugfix workflows

---

## The Five Rules

### Rule 1: Every Session Starts by Reading CLAUDE.md

**Action:** First thing in every session, read CLAUDE.md

**Why:** 
- CLAUDE.md is the only persistent memory across sessions
- Contains project status, completed tasks, blockers, decisions
- Without reading it, agents operate with stale context

**Check:**
- [ ] Read CLAUDE.md before starting work
- [ ] Understand current phase (BOOTSTRAP, BASELINE-AUDIT, ACTIVE-DEVELOPMENT)
- [ ] See which tasks are done, which are in progress
- [ ] Identify any blockers from previous sessions

**If CLAUDE.md is missing:**
```
This is the first session. Create CLAUDE.md with:
- Project identity
- Stack (languages, versions)
- Current status (BOOTSTRAP phase, no tasks yet)
- In Progress section (empty)
- Completed section (empty)
```

---

### Rule 2: Every Session Ends by Updating CLAUDE.md

**Action:** Last thing in every session, update CLAUDE.md

**What to update:**
- Last updated timestamp
- Current task state (DRAFT, PLANNED, IMPLEMENTED, VERIFIED, etc.)
- Completed tasks list (task-id, description, evidence reference, git hash)
- In progress section (task-id, description, current state, next step)
- Blocked section (if any new blockers discovered)
- New architecture decisions (if any)

**Template update:**

```markdown
Last Updated: [YYYY-MM-DD HH:MM:SS UTC] by [AGENT-ROLE]

## IN PROGRESS
- task-001 | Bootstrap Folder Structure | STATE: IMPLEMENTED | VERIFYING NOW
- task-002 | Agent Prompts (PLANNER...) | STATE: IN PROGRESS | WRITING PLANNER.MD

## COMPLETED
- task-001 | Bootstrap Folder... | .ases/architecture/decisions.md | commit-hash | 2026-06-27
```

**Never delete content** — only append or update state.

---

### Rule 3: No Session Claims Completion Without Evidence

**Forbidden Statements:**
- ✗ "Implementation complete"
- ✗ "Successfully implemented"
- ✗ "Fully tested"
- ✗ "Everything works"
- ✗ "Looks good"
- ✗ "Should work"
- ✗ "I ran the tests and they passed" (without log file reference)

**Required Claims:**
- ✓ "Implemented, unverified" — Code written, not yet verified
- ✓ "Verified: .ases/evidence/task-001/test-1719534330.log" — Evidence file referenced
- ✓ "Build passed (exit 0), see .ases/evidence/..." — Evidence-backed claim

**Rule:** Every completion claim must reference an evidence file or log output.

---

### Rule 4: After Implementation, Run Verification and Capture Output

**Process:**
1. After writing code/artifact, run the appropriate verification command
2. Capture output to a file (not just read it in the terminal)
3. **Read the output file** — do not summarize from memory
4. Report results based on what the file shows, not from memory

**Example (TypeScript):**

```bash
# After implementing, run:
tsc --noEmit src/agents/planner.md 2>&1 | tee .ases/evidence/task-002/build-$(date +%s).log

# Then READ the file:
cat .ases/evidence/task-002/build-*.log

# Report based on what's in the file:
"Build verification: EXIT code 0 (success)"
"See: .ases/evidence/task-002/build-1719534330.log"
```

**Why:**
- Prevents false confidence ("I think it passed" vs "the log shows it passed")
- Evidence file is the source of truth, not Claude's memory
- Human can spot-check log files independently

---

### Rule 5: Git Commit After Every Verified Unit

**When to commit:**
- After every task that's been implemented and verified
- Not after every tiny change
- Not every few hours (commits are meaningful units of work)

**Commit message format:**

```
[task-id]: [what was built]

Evidence: [log file or artifact reference]
Verification: [BUILD ✓ | LINT ✓ | TEST ✓ | etc.]
Status: [IMPLEMENTED, UNVERIFIED | VERIFIED, READY FOR X]

Co-Authored-By: Claude [Model] <noreply@anthropic.com>
```

**Example:**

```
task-001: Bootstrap folder structure and CLAUDE.md

Evidence: .ases/architecture/decisions.md created
         .ases/ directory structure verified with ls -R
Verification: Manual verification — folder structure complete
Status: IMPLEMENTED, READY FOR NEXT TASK

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

**Never force-push or amend public commits** — always create new commits.

---

## Phase 0 Task Workflow

```
PLANNER (Phase 0 session)
  reads: CLAUDE.md, FRD
  identifies next task
  breaks down what needs to be built
  updates CLAUDE.md: task → IN PROGRESS
    ↓
BUILDER (Phase 0 session)
  implements artifact (agent prompt, template, workflow, etc.)
  runs verification (if applicable: type check, line count, structure validation)
  updates CLAUDE.md: task → IMPLEMENTED
  git commits with evidence reference
    ↓
REVIEWER (Phase 0 session, fresh context)
  reads artifact
  checks against FRD requirements
  no false approval (thorough review required)
  updates CLAUDE.md: task → APPROVED
    ↓
HUMAN approves if satisfied, or sends back for revision
```

---

## No Skipping Steps in Phase 0

Even though Phase 0 is minimal, these rules are mandatory:

- ✓ Always read CLAUDE.md first
- ✓ Always update CLAUDE.md after
- ✓ Always verify work (even if just checking artifact exists and is not empty)
- ✓ Always commit with evidence reference
- ✓ Always get fresh-session review before marking done

**Do NOT:**
- ✗ Skip verification ("I'm confident it's right")
- ✗ Claim completion without evidence
- ✗ Commit without updating CLAUDE.md
- ✗ Self-review (someone else reads the artifact fresh)

---

## Bootstrap Status Vocabulary

Use only these terms:

```
DRAFT           — Task identified but not started
IN PROGRESS     — Currently being worked on
IMPLEMENTED     — Artifact built, awaiting verification
VERIFIED        — Verification run, evidence captured
APPROVED        — Independent review done, approved
COMMITTED       — Merged to git
BLOCKED         — Cannot proceed, reason documented
```

---

## Example Phase 0 Session

```
Session: Task 002 — Write PLANNER agent prompt

[Start of session]

1. Read CLAUDE.md
   ✓ Learned: Task 001 complete (committed 65edf60)
   ✓ Learned: Task 002 in progress
   ✓ Learned: Stack is ASES (Markdown + system prompts)

2. Identify work: Write .ases/agents/planner.md (PLANNER system prompt)

3. Implement
   ✓ Write 276-line prompt based on FRD Part 3.1
   ✓ Include role, reads, writes, forbidden actions, gates
   ✓ No placeholders

4. Verify artifact
   ✓ Check file exists: ls -1 .ases/agents/planner.md
   ✓ Check size: wc -l .ases/agents/planner.md (276 lines)
   ✓ Spot-check content: grep "Forbidden" .ases/agents/planner.md (found section)
   ✓ Evidence: "Manual verification — 276 lines, complete prompt structure"

5. Update CLAUDE.md
   Last Updated: 2026-06-27 23:30 UTC by BUILDER
   Task 002: Agent Prompts (PLANNER) | STATE: IMPLEMENTED | Ready for review

6. Commit
   git add .ases/agents/planner.md
   git commit -m "task-002: PLANNER agent prompt
   
   Evidence: .ases/agents/planner.md created (276 lines)
   Verification: Manual check — complete prompt, no placeholders
   Status: IMPLEMENTED, READY FOR REVIEW
   
   Co-Authored-By: Claude Haiku 4.5"

7. Independent Review (fresh session)
   REVIEWER reads planner.md
   Checks against FRD Part 3.1
   Confirms all required sections present
   Updates CLAUDE.md: task-002 → APPROVED

[End of session]
```

---

## When Bootstrap Phase Ends

Bootstrap phase (Phase 0) ends when:

1. ✓ All 9 tasks completed and verified
2. ✓ All `.ases/` components in place
3. ✓ All agent prompts written
4. ✓ All templates created
5. ✓ All workflows documented
6. ✓ ASES system is self-contained and ready to use

**Transition to Phase 1:**
- Run baseline audit on existing codebase (Ortho)
- Document known issues
- Accept as starting point
- Begin first feature under full ASES workflow

---

## Bootstrap Limitations (Known)

Phase 0 is minimal by design. These limitations are acceptable:

- No automated testing (Phase 0 is for infrastructure, not code)
- No peer review process (human manages all approvals)
- Solo developer (no true role separation)
- Manual verification (no CI/CD pipeline)
- Fresh CLAUDE.md each session (no cross-session memory except CLAUDE.md file)

These are handled by full ASES workflows once Phase 0 completes.

---

*End of bootstrap.md workflow*
