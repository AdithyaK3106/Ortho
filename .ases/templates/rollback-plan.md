# Rollback Plan

**Task ID:** [task-id]  
**Feature:** [feature name]  
**Created:** [YYYY-MM-DD]

---

## Rollback Trigger

[What conditions require rollback? Be specific.]

- Type errors detected in build (exit code ≠ 0 from `tsc --noEmit`)
- Linting failures (exit code ≠ 0 from `eslint`)
- Test failures (exit code ≠ 0 from `jest`)
- Regression failures (new test failures in regression suite)
- Critical issues found in code review
- Database migration fails
- Performance regression detected (endpoint response time >2x baseline)

---

## Rollback Procedure

[Exact git commands. Repeatable by someone who does not know the code.]

### Step 1: Identify the commit to revert

```bash
# Find the commit hash for this feature
git log --oneline | head -20
# Note the commit hash: [commit-hash]
```

### Step 2: Revert the commit

```bash
# Revert the commit (creates a new commit that undoes changes)
git revert [commit-hash]

# Or if the commit has not been pushed and you want to discard it:
git reset --hard [previous-commit-hash]
```

### Step 3: Verify rollback

```bash
# Ensure files are back to previous state
git log --oneline | head -5
git status
```

### Step 4: If database migration was applied

```bash
# Identify the migration files
ls -la src/database/migrations/

# Manually revert the migration (run the down migration)
# Example: If migration 001_create_categories_table.sql was applied
# Run the corresponding 001_drop_categories_table.sql (or equivalent)

# Or connect to database and run:
# DROP TABLE IF EXISTS categories CASCADE;
```

---

## Affected Components

[What breaks if we revert?]

- Users cannot create/manage categories for [duration of rollback]
- Expenses without categories will display as "Uncategorized" (if category_id becomes nullable)
- API endpoints /categories will return 404
- Any client code expecting category management will fail gracefully (should have fallback)

---

## Verification After Rollback

[How do we confirm rollback succeeded?]

### Code Verification
```bash
# Type checking passes
tsc --noEmit
# Exit code should be 0

# Linting passes
eslint .
# Exit code should be 0

# Tests pass
jest
# All tests should pass, no new failures

# Application starts
npm start
# Server starts without errors
```

### Database Verification
```bash
# Connect to database and verify categories table is gone
# PostgreSQL example:
# \dt categories
# Should return "Did not find any relation named "categories""

# Verify expenses table is still intact
# SELECT COUNT(*) FROM expenses;
# Should return a number (not error)
```

### Functional Verification
```bash
# Test that category endpoints no longer exist
curl -X GET http://localhost:3000/categories
# Should return 404

# Test that expense endpoints still work
curl -X GET http://localhost:3000/expenses
# Should return 200 with expenses list
```

---

## Known Rollback Limitations

[Be honest. What cannot be automatically rolled back?]

- **Data created during feature:** Any categories created by users while the feature was live cannot be automatically deleted. If rollback occurs:
  - Mitigation: Database table is dropped, so categories are deleted. Expenses with category_id will have dangling foreign keys.
  - Solution: Run migration to make category_id nullable, or cascade delete expenses with missing categories.

- **User activity logs:** If user activity was logged during the feature, those logs remain (cannot be unlogged).
  - Mitigation: Minimal risk if feature was short-lived.

- **Cache/CDN:** If category data was cached:
  - Mitigation: Clear cache manually if needed.

- **Third-party integrations:** If external systems were notified of categories:
  - Mitigation: Notify them of rollback, may require manual cleanup.

---

## Rollback Checklist

Before declaring rollback complete, verify:

- [ ] Commit reverted (git log shows revert commit)
- [ ] `tsc --noEmit` passes (exit 0)
- [ ] `eslint .` passes (exit 0)
- [ ] `jest` passes (no new failures)
- [ ] Application starts without errors
- [ ] Database is in clean state (categories table gone or migrated)
- [ ] Category endpoints return 404
- [ ] Existing endpoints still work
- [ ] Team notified of rollback

---

## Rollback Owner

[Who is responsible for executing rollback?]

- **Trigger authority:** Human developer (after reviewing verification-report.md or code review)
- **Executor:** Human (runs git and database commands)
- **Verifier:** VERIFIER agent (re-runs verification commands after rollback)

---

## Post-Rollback Action

[What happens after successful rollback?]

1. Create a new task for the revert (task-N-revert-category-management)
2. Analyze root cause (why did this feature fail verification?)
3. Update CLAUDE.md with known issues
4. PLANNER creates new plan addressing the root cause
5. Return to PLANNER workflow with updated plan

---

*End of rollback-plan.md template*
