# Plan — task-021-cli-copilot-commands

## Goal
Make the four engineering-copilot commands actually reachable by a pilot
user: `ortho guardrails [path]`, `ortho decide <intent>`, `ortho plan
<intent>`, `ortho refactor [path]` — registered in the `ortho` TypeScript
CLI, bridged to the real Python `CliCommands` class.

## Current State (the pilot-readiness gap)
- `CliCommands` (packages/cli-commands) is real, tested (100/100), and
  captures engineering memory (tasks 017-020) — but **has no CLI entry
  point at all**. The `ortho` bin (apps/cli) registers only: init, scan,
  index, analyze, run, status, approve, reject, history, context. A pilot
  user cannot invoke any copilot command without writing Python.
- The established bridge pattern already exists and works:
  `context.ts` (commander registration) -> `pybridge.ts`'s `runPython()`
  (spawns `python`/`python3` with inherited stdio) -> `context.py`
  (argparse `_main()` that sets sys.path for the monorepo packages, calls
  the real Python API, prints results). This task follows that exact
  pattern — no new architecture.

## Scope

### New: `apps/cli/src/commands/copilot.py`
Argparse bridge exposing all 4 commands. Mirrors `context.py`:
- sys.path bootstrap for every package `CliCommands` needs
  (shared/storage, repo-intelligence, arch-intelligence, impact-analysis,
  change-planner, feature-planner, refactoring-advisor, arch-guardrails,
  decision-engine, context-hub, cli-commands).
- Subcommands: `guardrails [--path P]`, `decide INTENT [--scan-path P]`,
  `plan INTENT [--scan-path P]`, `refactor [--path P]`.
- **Default path = the user's cwd** (passed explicitly by the TS side as
  `--path <cwd>` / `--scan-path <cwd>`, never left to Python-side cwd
  fallback) — this is the "seamless workflow" behavior: a pilot user cd's
  into their repo and runs `ortho guardrails` with no arguments.
- Prints `report.title`, blank line, `report.content`. Exit code 0 when
  `report.success` is True, 1 otherwise (scriptable).

### New: `apps/cli/src/commands/copilot.ts`
Four commander registrations calling `runPython("apps/cli/src/commands/
copilot.py", ...)`, passing `process.cwd()` as the default path/scan-path
when the user gives none. Registered in `apps/cli/src/index.ts`.

### Modified: `apps/cli/src/index.ts`
Import + `program.addCommand(...)` for the four new commands (or one
parent registration exporting four subcommands — BUILDER's judgment,
matching however commander idiom fits the existing file best; the four
must be **top-level** commands (`ortho guardrails`, not `ortho copilot
guardrails`) per the seamless-workflow requirement).

## Out of Scope
- Structured JSON output (`--format json`) — real future work for the MCP
  server (docs/mcp-server-contract.md §4), but a separate task; this task
  ships the human-facing text path only.
- Windows `.cmd` shim / npm publish / global install ergonomics — the
  existing `npm run build` + `bin` field already handles this the same
  way the other 10 commands do.
- Any change to `CliCommands` itself (its API is frozen as of task-020's
  commit; this task is purely additive exposure).

## Acceptance Criteria
1. `node apps/cli/dist/index.js guardrails --path repos/click` prints the
   real guardrails report and exits 0.
2. Same for `plan "add caching" --scan-path repos/click`,
   `refactor --path repos/click`, `decide "improve code quality"
   --scan-path repos/click`.
3. Running with no path from inside a repo directory scans that repo
   (cwd passed explicitly by TS side).
4. A failed command (nonexistent path, empty intent) prints the failure
   report and exits 1.
5. `tsc` build passes clean; existing jest tests unaffected.
6. Python bridge has pytest coverage (arg parsing -> correct CliCommands
   call -> exit-code mapping), following test_workflow_capture.py's
   real-fixture discipline (no mocking of CliCommands).
7. Real-repo verification: all 4 commands run end-to-end through the
   actual compiled TS CLI against repos/click.
