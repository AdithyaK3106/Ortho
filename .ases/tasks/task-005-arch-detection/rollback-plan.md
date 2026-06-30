# task-005: Rollback Plan

**Trigger:** Rejection at any gate or critical failure.

**Rollback procedures:**

### Gate 1–2 (Pre-code):
```bash
rm -rf .ases/tasks/task-005-arch-detection/
git status  # Should be clean
```

### Gate 3+ (After code committed):
```bash
git reset --hard HEAD~N  # Revert all task-005 commits
rm -rf .ases/tasks/task-005-arch-detection/
git branch -D task-005  # If on separate branch
```

### Full repo cleanup:
```bash
git reflog | grep task-005
git reset --hard <pre-task-sha>
```

---

**Prepared by:** PLANNER
