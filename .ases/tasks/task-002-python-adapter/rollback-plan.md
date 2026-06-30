task: task-002
title: Week 3–4 — Python Language Adapter
created: 2026-06-30

trigger:
  - Type errors (mypy --strict exit ≠ 0)
  - Lint failures (ruff check exit ≠ 0)
  - Test failures (pytest exit ≠ 0)
  - Regression failures (existing tests break)
  - Critical code review issues
  - tree-sitter Python grammar fails to load
  - Performance regression (symbol extraction >10s on 100KB file)

procedure: |
  # Step 1: Identify commit
  git log --oneline | head -20
  # Note [commit-hash] for task-002
  
  # Step 2: Revert
  git revert [commit-hash]
  
  # Step 3: Verify
  git log --oneline | head -5
  git status

affected_components:
  - repo-intelligence package removed (in development only)
  - LanguageAdapter interface not exported from shared/types
  - Python parsing capability unavailable during rollback (affects task-003)
  - No data loss (no database writes in this task)

verification_after_rollback: |
  tsc --noEmit (exit 0)
  ruff check . (exit 0)
  mypy --strict . (exit 0)
  pytest (all existing tests pass, 0 new failures)

limitations:
  - task-003 (call graph builder) depends on task-002 — will need redesign if rollback
  - tree-sitter grammar artifacts may remain in venv — manual cleanup may be needed

post_rollback_action: Create task task-002-revert-python-adapter. PLANNER analyzes root cause. BUILDER fixes in new session.

---
