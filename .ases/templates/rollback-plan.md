task: [task-id]
title: [task-title]
created: [YYYY-MM-DD]

trigger:
  - Type errors (tsc exit ≠ 0)
  - Lint failures (eslint exit ≠ 0)
  - Test failures (jest exit ≠ 0)
  - Regression failures (new test failures)
  - Critical code review issues
  - Database migration fails
  - [custom triggers]

procedure: |
  # Step 1: Identify commit
  git log --oneline | head -20
  # Note [commit-hash]
  
  # Step 2: Revert
  git revert [commit-hash]
  
  # Step 3: Verify
  git log --oneline | head -5
  
  # Step 4: Database (if applicable)
  # DROP TABLE [table_name] CASCADE;
  # Or run down migration: [migration-down-script]

affected_components:
  - [component 1 — impact]
  - [component 2 — impact]
  - [component N]

verification_after_rollback: |
  tsc --noEmit (exit 0)
  eslint . (exit 0)
  jest (no new failures)
  npm start (no errors)
  [database checks]

limitations:
  - [limitation 1] — mitigation: [how to handle]
  - [limitation 2] — mitigation: [...]
  - [limitation N]

post_rollback_action: Create task [N]-revert-[reason]. Analyze root cause. PLANNER plans fix.

---
