# Plan — task-022-structured-json-output

## Goal
Add structured JSON output to `CliCommands.guardrails()` and `.decide()` 
so Claude Code and other tool consumers (MCP servers, CI systems) can 
programmatically access violations, recommendations, and evidence — not 
just parse human-readable text.

## Current State
- `CliReport` (packages/cli-commands/src/cli_commands/types.py) has only:
  `title: str`, `content: str`, `format: str`, `success: bool`.
- `guardrails()` and `decide()` format all structured findings into text 
  via `"\n".join(...)` — violations and recommendations are lost after 
  formatting, unretrievable by a caller.
- `plan()` and `refactor()` return text only; their structured objects 
  (`ImplementationPath`, `RefactoringIssue`) are not exposed. Out of scope 
  for this task (MCP contract §4 names only guardrails/decide).

## Scope

### New: structured fields in CliReport
Extend `CliReport` (packages/cli-commands/src/cli_commands/types.py) with 
optional fields:
- `violations: list[GuardrailViolation] | None` — for guardrails results
- `recommendations: list[Recommendation] | None` — for decide results
- Both default to `None` (backward-compatible: existing callers see no change)
- Type imports from `arch_guardrails.types` and `decision_engine.types`

### Modified: guardrails() and decide() in CliCommands
Both methods now populate the new structured fields alongside text content:
- `guardrails()`: call `ArchitectureEnforcer.check_violations()` (already 
  happens), capture the real `violations: list[GuardrailViolation]`, 
  format to text for `content`, and assign to `report.violations`.
- `decide()`: call `DecisionEngine.decide()` (already happens), capture 
  the real `decision: Decision` object, extract 
  `decision.options + decision.recommended_option`, format to text for 
  `content`, and assign to `report.recommendations`.

### Unchanged
- `plan()` and `refactor()` stay text-only (out of scope per MCP contract).
- Text output (`content` field) is identical to today — no reformatting, 
  no breaking changes to CLI output.
- CLI commands (copilot.ts, copilot.py) are not changed — they print 
  `report.content` to stdout exactly as before.
- `.ortho/ortho.db` workflow_run capture is unchanged.

## Acceptance Criteria
1. `CliReport` type is extended with optional `violations` and 
   `recommendations` fields, both default `None`.
2. `guardrails()` populates `report.violations` with real 
   `GuardrailViolation` objects from the enforcer.
3. `decide()` populates `report.recommendations` with real 
   `Recommendation` objects from the decision engine.
4. Text content is *identical* to pre-task output (no reformatting).
5. A Python caller can do: 
   ```python
   report = CliCommands().guardrails(path)
   if report.violations:
       for v in report.violations:
           print(f"{v.rule_id}: {v.message}")
   ```
6. All existing 100/100 cli-commands tests still pass (no regressions).
7. New tests verify the structured fields are present and correct:
   - `guardrails()` against a real bounded repo yields non-None violations
   - `decide()` against a real bounded repo yields non-None recommendations
8. MPC server contract (docs/mcp-server-contract.md) is updated with the 
   new JSON shape (as an appendix, not changing existing prose).

## Out of Scope
- Changing text output format or content.
- Adding structured output to `plan()` or `refactor()`.
- JSON serialization of CliReport itself (that's MCP server work).
- CLI flag `--format json` (deferred; copilot.ts stays unchanged).
