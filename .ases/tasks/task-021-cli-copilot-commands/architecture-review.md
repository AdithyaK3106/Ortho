# Architecture Review — task-021-cli-copilot-commands

**Verdict:** APPROVED

## Layer Compliance (ADR-015 / ADR-016)
`apps/cli` (Apps layer) spawning a Python bridge that imports
`cli_commands` (also Apps layer per ADR-016) is exactly the existing,
already-reviewed pattern: `context.ts` -> `pybridge.ts` -> `context.py`
-> `context_hub`. The new `copilot.py` bridge imports only
`cli_commands.commands.CliCommands` — it does not reach past the Apps
layer into Engineering-Copilot or Intelligence packages directly, which
keeps the single integration seam ADR-016 and docs/mcp-server-contract.md
§6 both prescribe ("never import directly from
repo-intelligence/arch-intelligence/arch-guardrails itself").

No new layer, no new ADR, no new dependency direction. The sys.path
bootstrap in `copilot.py` lists the transitive packages `cli_commands`
needs at import time — that is environment plumbing (same as
`context.py`'s existing bootstrap), not an architectural import.

## Pattern Fidelity Check (user constraint)
Verified against the real files this review read directly:
- `pybridge.ts`: `runPython()` spawns with `stdio: "inherit"` (stderr
  passthrough preserved for free), python -> python3 ENOENT fallback,
  rejects on nonzero exit. `copilot.ts` reuses it unchanged.
- `context.ts`: `const CONTEXT_CLI = "apps/cli/src/commands/context.py"`
  + commander `.command()` + try/catch -> stderr + `process.exit(1)`.
  `copilot.ts` mirrors this shape per command.
- `context.py`: `_PROJECT_ROOT = Path(__file__).resolve().parents[4]`,
  sys.path insert loop, argparse `_main()`, `sys.exit(0/1)`.
  `copilot.py` mirrors it, with the exit code driven by
  `report.success` instead of exception-only.

## Data Flow
`ortho guardrails [path]` -> commander action (TS validates intent
where applicable, resolves default path = `process.cwd()`) ->
`runPython("apps/cli/src/commands/copilot.py", [...])` -> argparse ->
`CliCommands().guardrails(path)` -> print title + content ->
`sys.exit(0 if success else 1)` -> `runPython` resolves/rejects ->
CLI exit code.

One nuance flagged for BUILDER: `runPython` rejects on any nonzero exit
with the generic message `"Command failed with exit code 1"`. For a
failed *report* (success=False), the report text has already been
printed to stdout by the Python side before exit — so the TS catch
should exit 1 **without** printing the generic rejection message as an
"Error:" (that would mislabel a clean, expected failure report as a
CLI crash). BUILDER should distinguish: spawn-level errors (ENOENT,
unparseable args) -> print error; report-level failure (exit 1 after
output was already shown) -> just exit 1. Simplest compliant approach:
catch, and only print the message when it is not the generic
exit-code-1 rejection — or use a distinct exit code convention. This is
a UX-correctness detail, not an architecture change; resolving it inside
`copilot.ts` keeps `pybridge.ts` untouched (user constraint: no changes
to existing behavior).

## Blast Radius
Two new files + import/registration lines in `index.ts`. Zero Python
package changes. Existing 10 commands untouched.

## Verdict
APPROVED — no ADR needed, follows the established bridge pattern
verbatim, all user constraints from GATE 1 are architecturally sound and
incorporated.
