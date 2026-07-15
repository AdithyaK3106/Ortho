# Spec — task-021-cli-copilot-commands

## CLI Surface (user-facing contract)

```
ortho guardrails [path]                  # architecture violation check
ortho decide <intent> [--scan-path P]    # decision support (intent = text or file path)
ortho plan <intent> [--scan-path P]      # feature implementation paths
ortho refactor [path]                    # refactoring findings
```

- `path` / `--scan-path` default: the user's current working directory
  (resolved by the TS layer via `process.cwd()` and passed explicitly —
  the Python bridge always receives an explicit path, never falls back
  to its own cwd).
- Output: `report.title`, blank line, `report.content` — plain text to
  stdout, exactly what `CliCommands` returns, no reformatting.
- Exit code: `0` iff `report.success` is True, else `1`.
- Errors from the bridge itself (bad python env, unparseable args) exit
  nonzero with a message on stderr — same behavior as the existing
  `context.ts`/`runPython` path.

## Python bridge: `apps/cli/src/commands/copilot.py`

```
python copilot.py guardrails --path <dir>
python copilot.py decide <intent> --scan-path <dir>
python copilot.py plan <intent> --scan-path <dir>
python copilot.py refactor --path <dir>
```

- `--path`/`--scan-path` are required at the bridge level (the TS side
  always supplies them) — keeps the no-unbounded-scan discipline from
  tasks 017/019 mechanical rather than convention.
- sys.path bootstrap before imports, mirroring `context.py`'s existing
  `_PROJECT_ROOT` pattern, covering all 11 packages `CliCommands`
  transitively needs.
- Calls `CliCommands().guardrails(path)` / `.decide(intent,
  scan_path=...)` / `.plan(intent, scan_path=...)` / `.refactor(path)`.
- `sys.exit(0 if report.success else 1)`.

## TypeScript: `apps/cli/src/commands/copilot.ts`

Four `Command` exports (or one module exporting four), registered
top-level in `index.ts`. Each action: build args array (always including
the explicit path, defaulting to `process.cwd()`), `await
runPython(COPILOT_CLI, args)`, catch -> stderr + `process.exit(1)`.
`runPython` already propagates the child's exit code as a rejection on
nonzero, so failed reports (bridge exit 1) surface as CLI exit 1 without
extra plumbing.

**Constraints locked at GATE 1 approval (user-specified):**
- Follow `context.ts` -> `pybridge.ts` -> `context.py` pattern exactly;
  no new abstractions.
- Purely additive: zero changes to `CliCommands` or any existing command.
- Reuse `runPython`'s existing python -> python3 discovery, unchanged.
- **`plan`/`decide` must validate empty/whitespace intents in the TS
  layer, before spawning Python** — print a clear error to stderr and
  exit 1 without a wasted subprocess round-trip. (The Python side's own
  rejection remains as defense-in-depth; the TS check is the fast path.)
- Preserve stderr passthrough (`stdio: "inherit"` via `runPython`).
- Four top-level Commander commands.

## Behavior table

| Invocation | Result |
|---|---|
| `ortho guardrails` (inside a repo) | scans cwd, prints report, exit 0 |
| `ortho guardrails /bad/path` | failure report, exit 1 |
| `ortho plan ""` | `plan()` rejects empty intent -> failure report printed, exit 1 |
| `ortho decide src/core.py` (real file) | change-impact analysis on that file's parent dir |
| `ortho refactor` on a clean repo | "No refactoring issues found.", exit 0 |

## Non-Goals
- `--format json` (future task, MCP contract §4).
- Any subcommand nesting (`ortho copilot X`) — commands are top-level.
- Changes to `CliCommands` or any Python package under `packages/`.

## Real-Repo Verification Target
`repos/click` via the actual compiled CLI (`npm run build` then
`node apps/cli/dist/index.js ...`) — not just the Python bridge in
isolation.
