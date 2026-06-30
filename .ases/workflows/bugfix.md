# Bug Fix Workflow

**Version:** 1.0  
**Source:** ASES FRD v1.1, Part 7.2  
**Purpose:** Simplified workflow for bug fixes (skips ARCHITECT unless the fix touches architecture)

---

## Overview

Bug fixes follow the standard feature workflow (Part 7.1) except:
- **ARCHITECT review is optional** — Only required if the fix changes module boundaries, APIs, schemas, or security
- **All other gates remain mandatory** — Plan, code, tests, verification, review

---

## Workflow Sequence

```
HUMAN describes bug with exact reproduction steps
    ↓
PLANNER session
  reads: CLAUDE.md, bug report, codebase
  produces: plan.md (root cause analysis) + spec.md (fix scope) + rollback-plan.md
  task state: DRAFT → PLANNED
    ↓
[GATE 1: Plan Approval]
    ↓
Human reviews plan, spec, rollback-plan
    ↓ APPROVED
[Decision Point: Does this fix touch architecture?]
    ↓
[If NO → Skip ARCHITECT]
    ↓
[If YES → Run ARCHITECT session]
    ↓
ARCHITECT session (if needed)
  produces: architecture-review.md
    ↓
[GATE 2: Architecture Approval] (if ARCHITECT ran)
    ↓
BUILDER session
  reads: spec.md, rollback-plan.md
  produces: production code fix + implementation-notes.md
  task state: READY-TO-BUILD → IMPLEMENTED
    ↓
[GATE 3: Scope Review]
    ↓
Human reviews implementation-notes.md
    ↓ NO VIOLATIONS
TEST-DESIGNER session (independent, fresh context)
  produces: tests + test-plan.md
  task state: IMPLEMENTED → TESTS-WRITTEN
    ↓
[GATE 4: Test Coverage Review]
    ↓
VERIFIER session
  produces: verification-report.md + evidence-package.md
    ↓
[GATE 5: Evidence Review]
    ↓
REVIEWER session (independent, fresh context)
  produces: review.md
    ↓
Human commits with evidence reference
  task state: APPROVED → COMMITTED
```

---

## Key Differences from Feature Workflow

### ARCHITECT Review Is Optional

**Question:** Does this fix change architecture?

**Criteria for "YES" (requires ARCHITECT):**
- ✓ Changes module boundaries (splits/merges modules)
- ✓ Changes API contracts (new endpoint, signature change)
- ✓ Changes database schema (new table, column, constraint)
- ✓ Changes security approach (new validation, access control)
- ✓ Violates or modifies existing ADRs

**Criteria for "NO" (skip ARCHITECT):**
- ✗ Bug fix within existing module (code fix only)
- ✗ Adding defensive checks (input validation)
- ✗ Fixing exception handling (error path improvement)
- ✗ Optimizing query (same logic, better performance)
- ✗ Fixing typos, style issues, comments

**Decision Logic:**
```
IF fix changes module structure, APIs, schema, or security
  THEN run ARCHITECT review
ELSE skip to BUILDER
END
```

### Root Cause Analysis in plan.md

PLANNER **must** include root cause analysis in plan.md:

```markdown
## Root Cause Analysis

**Bug:** Users cannot delete categories if they have expenses

**Symptoms:**
- DELETE /categories/cat-123 returns 409 Conflict
- Error message: "Cannot delete category with expenses"
- Affects all users

**Root Cause:** 
CategoryService.deleteCategory() validates that category has no expenses before deletion.
This validation is correct (by design), but API error message is misleading.
Users expect 400 Bad Request with specific reason, not 409 Conflict.

**Why It Happened:**
- BUILDER implemented validation in deleteCategory()
- Error thrown: CATEGORY_HAS_EXPENSES
- Controller catches and returns 409
- But spec says this should be 400 (client error, not conflict)

**Impact:** Users cannot understand why delete fails. Error message says "conflict" but means "has active expenses."
```

---

## Fix Scope in spec.md

PLANNER **must** define fix scope precisely:

```markdown
## Fix Scope

**What This Fix Does:**
- Change DELETE /categories/:id error from 409 to 400 when category has expenses
- Update error code from CATEGORY_HAS_EXPENSES to INVALID_REQUEST
- Update error message to "Cannot delete category with active expenses. Delete all expenses first."

**What This Fix Does NOT Do:**
- Does NOT change business logic (category with expenses still cannot be deleted)
- Does NOT change database schema
- Does NOT create new endpoints
- Does NOT modify any other category endpoints

**Files That Will Change:**
- src/controllers/CategoryController.ts (error response mapping)
- src/services/CategoryService.ts (error message text)
- No other files

**Files That Must NOT Change:**
- Database schema
- API contract (still validates category has no expenses)
- Existing tests (should still pass)
```

---

## Testing Strategy for Bug Fixes

TEST-DESIGNER **must** include:

1. **Regression test** — Verify the bug no longer occurs
2. **Edge case tests** — Verify fix handles boundary conditions
3. **Existing tests pass** — Verify no new breakage

Example test-plan.md:

```markdown
## Bug Regression Test

### Bug: DELETE /categories/:id returns 409 instead of 400 for "has expenses"

**Test:** test_delete_categories_with_expenses_returns_400
- Create category
- Create expense with that category
- DELETE /categories/[id]
- Expected: 400 (not 409)
- Expected error code: INVALID_REQUEST (not CATEGORY_HAS_EXPENSES)

## Regression: Ensure Fix Doesn't Break Anything

- test_delete_categories_still_prevents_deletion_if_expenses_exist
  → Verify business logic: cannot delete if expenses exist (still true)
- test_delete_categories_empty_still_succeeds
  → Verify delete works for empty categories
- test_all_other_category_endpoints_unchanged
  → Verify POST, GET, PUT still work

## Existing Test Coverage

- All existing category tests should still pass (0 new failures)
```

---

## When Bug Fix Requires ARCHITECT

### Example 1: Bug in Error Handling (skip ARCHITECT)

**Bug:** Null pointer exception when creating category with null description

**Fix:** Add null check before accessing description field

**ARCHITECT needed?** NO
- Fix is within existing module
- No API change
- No schema change
- No security impact
- Skip ARCHITECT, go to BUILDER

### Example 2: Bug in Category Deletion (skip ARCHITECT)

**Bug:** DELETE /categories/:id returns wrong error code

**Fix:** Change error response from 409 to 400

**ARCHITECT needed?** NO
- Fix is within existing module
- API contract unchanged (same endpoint, same validation)
- No schema change
- No security impact
- Skip ARCHITECT, go to BUILDER

### Example 3: Bug Requiring Schema Fix (ARCHITECT needed)

**Bug:** Category names should be case-insensitive but currently are case-sensitive

**Fix:** Add LOWER() function to database unique constraint

**ARCHITECT needed?** YES
- Touches database schema (adds new constraint behavior)
- May require migration
- Affects data integrity rules
- Run ARCHITECT to review schema change

### Example 4: Bug in Security Validation (ARCHITECT needed)

**Bug:** Input validation allows SQL injection in category name

**Fix:** Add parameterized query check (or was already parameterized but not validated)

**ARCHITECT needed?** YES
- Touches security approach
- May require validation layer redesign
- Run ARCHITECT to review security fix

---

## Commit Message for Bug Fixes

After REVIEWER approves:

```
[task-id]: Fix [bug description]

Bug: [What was broken]
Root Cause: [Why it was broken]
Fix: [What changed to fix it]

Evidence: .ases/evidence/[task-id]/
Gates: BUILD ✓ LINT ✓ TESTS ✓ REGRESSION ✓ REVIEW ✓
Confidence: EVIDENCE-BACKED

Co-Authored-By: Claude [Model] <noreply@anthropic.com>
```

---

## Fast Track for Trivial Bugs

**Condition:** Bug is extremely simple (typo, obvious one-liner fix)

**Process:**
1. PLANNER creates minimal plan.md (root cause + fix scope)
2. BUILDER makes fix (1-2 lines)
3. TEST-DESIGNER writes 2-3 tests
4. VERIFIER verifies
5. REVIEWER approves

**Minimum gates still required:** All 5 gates still apply. No shortcuts. Even trivial bugs need evidence.

---

## Rollback for Bugs

If bug fix causes regression:

1. Use rollback-plan.md to revert
2. Analyze why fix introduced regression
3. PLANNER creates new bug fix task addressing the root cause more carefully
4. Start workflow over

---

*End of bugfix.md workflow*
