# Feature Plan

**Task ID:** [task-id]  
**Feature Name:** [feature name]  
**Owner:** [Solo Developer]  
**Created:** [YYYY-MM-DD]  
**Last Updated:** [YYYY-MM-DD]

---

## Feature Summary

[2-3 sentences describing what this feature does and why it matters]

Example:
> This feature adds expense category management (CRUD operations) to the system, allowing users to create, read, update, and delete spending categories. This is foundational for the expense tracking system, enabling categorized expense records in Phase 2.

---

## Atomic Task Breakdown

Break the feature into 30-90 minute units. Each task is independent enough for one BUILDER to complete in one session.

### Task 1: [Task Title]
- **Scope:** [What changes? What files are affected?]
- **Duration:** 30-60 minutes
- **Dependencies:** [What must be complete before this task starts?]
- **Acceptance Criteria:**
  - [ ] Criterion 1
  - [ ] Criterion 2
  - [ ] Criterion 3

### Task 2: [Task Title]
- **Scope:** [What changes?]
- **Duration:** 45-75 minutes
- **Dependencies:** Task 1 must be complete
- **Acceptance Criteria:**
  - [ ] Criterion 1
  - [ ] Criterion 2

### Task 3: [Task Title]
- **Scope:** [What changes?]
- **Duration:** 45-90 minutes
- **Dependencies:** Task 2 must be complete
- **Acceptance Criteria:**
  - [ ] Criterion 1
  - [ ] Criterion 2

---

## Task Dependency Order

Visualize the dependencies:

```
Task 1 (schema design)
    ↓
Task 2 (service layer)
    ↓
Task 3 (API endpoints)
    ↓
Task 4 (validation) [can run in parallel with Task 3 if needed]
```

---

## Risk Identification

What could go wrong?

- **Risk 1: [Title]** — [What could fail] — [Impact] — [Mitigation]
- **Risk 2: [Title]** — [What could fail] — [Impact] — [Mitigation]
- **Risk 3: [Title]** — [What could fail] — [Impact] — [Mitigation]

Example:
- **Risk: Breaking existing expense queries** — If category schema changes, existing GET /expenses may break — [Impact: Users cannot fetch expenses] — [Mitigation: Add backward-compatible query support, verify with regression tests]

---

## Feature-Level Acceptance Criteria

This feature is "done" when ALL these are true:

- [ ] All atomic tasks completed and verified
- [ ] No new type errors introduced
- [ ] No new linting errors introduced
- [ ] All new tests pass
- [ ] No regression test failures
- [ ] Architecture review approved (if required)
- [ ] Code review approved
- [ ] All evidence files exist and are verified

---

## Notes for ARCHITECT

[Any architectural considerations? New modules? New dependencies? Security questions? This section is for flagging items that require architecture review.]

Example:
> - New module: CategoryService (data layer abstraction)
> - New database table: categories
> - New API: POST /categories, GET /categories, PUT /categories/:id, DELETE /categories/:id
> - Security: Validate category ownership before allowing delete

---

## Notes for BUILDER

[Any implementation guidance or constraints? Any known edge cases?]

Example:
> - Use TypeScript for type safety
> - Follow existing ExpenseService pattern for consistency
> - Validate category names (max 100 chars, no special characters)
> - Handle concurrent creates gracefully

---

*End of plan.md template*
