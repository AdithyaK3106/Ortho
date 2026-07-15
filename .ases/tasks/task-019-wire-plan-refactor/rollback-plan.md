# Rollback Plan — task-019-wire-plan-refactor

## Blast Radius
- New files: `cli_commands/feature_plan_adapter.py`, `cli_commands/refactor_adapter.py`.
- Modified: `cli_commands/commands.py` (`plan()`/`refactor()` method bodies only).
- No changes to `feature-planner`, `refactoring-advisor`, `impact-analysis`,
  `arch-guardrails`, `change-planner`, or any already-wired `guardrails()`/
  `decide()` code paths.
- Sole consumer of `CliCommands` is the CLI entry point (same blast radius
  class as task-017/018).

## Rollback Procedure
If a regression is found post-merge:
1. `git revert <task-019 commit>` — the two new adapter files and the
   `commands.py` method-body changes are fully self-contained; reverting
   restores the prior hardcoded-stub behavior with no side effects on any
   other package.
2. No data migrations, no schema changes, no ContextHub writes in this
   task (task-020 only) — rollback is a pure code revert.

## Risk Assessment
Low. Purely additive (new adapters) plus two isolated method-body swaps in
a class with no other internal state. Same risk profile as task-017, which
had zero rollback incidents.
