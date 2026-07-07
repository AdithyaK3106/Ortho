# task-012: Intent Routing + Registries — Rollback Plan

## Trigger

GATE 5 (VERIFIER) produces evidence that code does not meet acceptance criteria.

## Rollback Procedures

### Local Repository (not yet pushed)

1. **Identify commits:** `git log --oneline | head -7` — find the 7 task-012 commits (Tasks 1–7).
2. **Hard reset:** `git reset --hard <commit-before-task-1>` (typically the GATE 1 approval commit for task-012's own artifacts).
3. **Verify:** `git status` shows clean working tree. `python -c "import packages.orchestration"` should fail or import only empty `__init__.py`.

### Published to Main Branch (after PR merge)

Not applicable — task-012 is under active development; rollback only applies if VERIFIER gate fails locally.

## Order of Reverts (dependencies)

If local rollback needed:

1. Task 7 (pyproject.toml edits) — depends on Task 6 (ADR-013)
2. Task 6 (ADR-013) — standalone, reverted via `git revert`
3. Task 5 (intent/classifier.py stub) — depends on Task 4 (router exists)
4. Task 4 (intent/router.py) — standalone; delete directory and revert pyproject edits
5. Task 3 (agent/skill .md files) — depends on Tasks 1–2 (registries exist to validate against)
6. Task 2 (SkillRegistry) — delete `packages/orchestration/src/orchestration/selector/`
7. Task 1 (AgentRegistry) — delete entire `packages/orchestration/src/orchestration/` subdirectory structure

Reverse order: 7 → 6 → 5 → 4 → 3 → 2 → 1.

## Verification After Rollback

Run the same import/test suite that would pass before task-012:

```bash
# Pre-task-012 state should show:
# - packages/orchestration/ exists but only has empty pyproject.toml + .gitignore
# - no src/ directory
# - no .ases/agents/core/, .ases/skills/core/ directories (or they contain only stub agent/skill .md files)
# - no new dependencies in pyproject.toml

python -c "import packages.orchestration" # Should fail or import empty package
pytest packages/repo-intelligence/tests/ -q  # Should pass (85+ tests)
pytest packages/context-hub/tests/ -q        # Should pass (54+ tests)
pytest packages/arch-intelligence/tests/ -q  # Should pass (76 tests)
pytest packages/impact-analysis/tests/ -q    # Should pass (42 tests)
pytest 2>&1 | grep -E "passed|failed"        # All suites except orchestration should pass
```

Expected: All pre-task-012 tests pass; no breakage in other packages.

## Failure Modes

**Import failure on `python -c "import semantic_router"`:** If rollback incomplete and Task 7 partially reverted. Verify `packages/orchestration/pyproject.toml` has no `semantic-router` line; re-run Task 2 rollback.

**`.ases/agents/core/` directory not removed:** If Task 3 reverted but directory left behind. Manually `rm -rf .ases/agents/core/` and `.ases/skills/core/` if they contain only stub files.

**ADR-013 still in `.ases/architecture/adrs/`:** If Task 6 not reverted. Run `git revert <ADR-013-commit>` or manually delete the file (safe to delete since it's metadata, not code).

## Timeline

Rollback Steps 1–3: ~2 minutes (git operations).
Verification: ~5 minutes (test suite runs).
Total: ~7 minutes.

## Recovery Path

After rollback:
1. PLANNER reviews failure evidence (from `.ases/evidence/task-012/`).
2. Identify whether failure is in registries, router, agent/skill authoring, or test design.
3. Open GATE 1 review and modify `plan.md`/`spec.md` if scope needs adjustment.
4. Proceed to ARCHITECT for revised architecture review.
5. BUILDER redoes Tasks 1–7 with fixes.
