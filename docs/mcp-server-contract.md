# Ortho MCP Server — Interface Contract

**Purpose:** This doc specifies the exact tool names, input schemas, and output
shapes the MCP server must expose, so it wraps ortho's real Python engine
instead of a guessed interface. Every schema below is taken directly from
code that exists and passes tests today (`packages/cli-commands`,
`packages/arch-guardrails`, `packages/decision-engine`, `packages/change-planner`)
— not aspirational.

**Status:** ortho's Python side (`CliCommands` class) is the source of truth.
The MCP server is a thin wrapper that calls into it (via a Python subprocess,
`apps/cli/src/commands/pybridge.ts`-style bridge, or direct in-process call
if the MCP server is itself Python). It should not reimplement any analysis
logic — only marshal inputs/outputs.

---

## 1. Why MCP, and what "seamless" means here

Right now a developer runs `ortho guardrails <path>` from a separate
terminal, reads text output, and manually brings findings back into their
Claude Code conversation. MCP removes that round-trip: Claude Code calls the
tool directly mid-conversation and gets structured results back.

**Latency target:** <2 seconds per call (per project strategy notes) — this
constrains scan scope (see §5, Known Constraints).

---

## 2. Tools to Expose

**All four tools are real as of 2026-07-15** (`plan`/`refactor` were wired
to their real engines in task-019 — the earlier §3 warning no longer
applies and has been replaced with the new tools' schemas).

**Side effect to know about (task-020):** every call to any of the four
commands now also writes a `workflow_run` memory artifact into
`<scanned_root>/.ortho/ortho.db` (best-effort; failures are swallowed and
never affect the returned report). The MCP server doesn't need to do
anything about this, but the scanned repo gaining a `.ortho/` directory
is expected behavior, not a bug.

### 2.1 `ortho_guardrails`

**Wraps:** `CliCommands.guardrails(path: str | None = None) -> CliReport`
(`packages/cli-commands/src/cli_commands/commands.py`)

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Absolute or relative path to the repository (or subdirectory) to scan. Defaults to current working directory if omitted."
    }
  },
  "required": []
}
```

**What it does (real behavior, verified):**
1. Walks `path` for `.py` files (excludes `.`-prefixed dirs, `node_modules`, `venv`, `.venv`, `env`, `__pycache__`, `site-packages`, `dist`, `build`, `vendor`)
2. Builds real call graph, import graph, symbol table (`repo-intelligence`)
3. Detects architecture layers (`arch-intelligence`)
4. Runs `ArchitectureEnforcer.check_violations()` — real checks: layer boundary violations, circular dependencies, module size limits (>500 lines or >50 functions)
5. Returns real `GuardrailViolation` objects, not canned text

**Output shape (`CliReport`):**
```json
{
  "title": "string",
  "content": "string",
  "format": "text",
  "success": true
}
```

`content` is currently human-readable text, one violation per line:
```
[error] layer_boundaries at core → types: Business cannot import Data -> Invert dependency or use abstraction
[warning] module_sizing at core: Module exceeds 500 lines (3681) -> Split into focused modules
```
or, if scan succeeded with zero violations:
```
Scanned 76 file(s). No violations found.
```

**⚠️ For MCP, request structured output instead of text.** See §4 — this is
the one required change before wrapping this tool.

**Failure modes (real, tested):**
- Path doesn't exist → `{"success": false, "content": "Path does not exist: <path>", ...}`
- Any internal scan error → `{"success": false, "content": "Scan failed: <error>", ...}`
- Never raises — always returns a `CliReport`, even on failure.

---

### 2.2 `ortho_decide`

**Wraps:** `CliCommands.decide(intent: str, scan_path: str | None = None) -> CliReport`

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "intent": {
      "type": "string",
      "description": "Either a real file path (triggers change-impact analysis) or a free-text description of an intended change (falls back to guardrails-only aggregation). Must be non-empty."
    },
    "scan_path": {
      "type": "string",
      "description": "Bounded directory to scan when intent is free text (not a file path). Ignored if intent is itself a file path (its parent directory is used instead). Strongly recommended — see Known Constraints §5."
    }
  },
  "required": ["intent"]
}
```

**What it does (real behavior, verified):**
- If `intent` is a real file path: scans that file's parent directory, runs `ChangePredictor.predict_impact()` (real call-graph/import-graph traversal to find blast radius) plus `ArchitectureEnforcer.check_violations()`, aggregates both via `DecisionEngine.decide()`.
- If `intent` is free text: scans `scan_path` (or cwd if omitted — see constraint below), runs guardrails-only, aggregates via `DecisionEngine`.
- Empty string `intent` → rejected immediately, `success: false` (does not scan).

**Output shape:** same `CliReport` shape as above. `content` currently:
```
Decision for: <intent>

Recommended: <top recommendation title>
<reasoning string>
Alternatives: <comma-separated alternative titles>
```

**Failure modes (real, tested):**
- Empty intent → `{"success": false, "content": "Cannot decide on an empty intent.", ...}`
- Nonexistent scan path → `{"success": false, "content": "Path does not exist: <path>", ...}`

---

## 3. `ortho_plan` and `ortho_refactor` (real as of task-019, 2026-07-15)

### 3.1 `ortho_plan`

**Wraps:** `CliCommands.plan(intent: str, scan_path: str | None = None) -> CliReport`

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "intent": {
      "type": "string",
      "description": "Free-text description of the feature to plan. Must be a non-empty string (empty or non-string intents are rejected with success=false, no scan)."
    },
    "scan_path": {
      "type": "string",
      "description": "Bounded directory to scan. Strongly recommended (defaults to cwd -- see Known Constraints §5)."
    }
  },
  "required": ["intent"]
}
```

**What it does (real behavior, verified):** classifies the intent into a
feature type (endpoint / service / data_layer / cross_cutting /
infrastructure) via `FeaturePlanner`, then returns >=3 genuinely distinct
implementation paths (name, effort, risk, rationale each). Output varies
by intent classification — not a fixed template.

**`content` example:**
```
Feature type: cross_cutting

- Decorator/Middleware (effort=low, risk=low): Add via function decorator or middleware -> Minimal invasiveness, reusable
- Centralized Service (effort=medium, risk=low): Dedicated service instance -> Centralized management and configuration
- Aspect-Oriented (effort=high, risk=medium): Aspect injection at runtime -> Complete separation, powerful but complex
```

### 3.2 `ortho_refactor`

**Wraps:** `CliCommands.refactor(path: str | None = None) -> CliReport`

**Input schema:** same single-`path` shape as `ortho_guardrails` (§2.1).

**What it does (real behavior, verified):** real bloat detection
(modules >300 lines or >20 functions, measured from actual source), real
tight-coupling and circular-dependency detection (DFS over the real
import graph). Findings on `repos/click` correctly identify its
genuinely large modules (`core.py`, `types.py`).

**Honest-gap note:** duplication detection and churn analysis return
nothing (no code-similarity detector or git-history integration exists
yet — deliberately empty rather than fabricated; see task-019 spec).
Don't present "no duplication findings" as "no duplication exists."

**`content` example:**
```
[high] bloat at src.click.core: Split into focused modules (effort=1-2 days, confidence=1.00)
```
or `No refactoring issues found.` on a clean repo (success=true — a
clean repo is a valid outcome, not an error).

---

## 4. Required Change Before MCP Integration: Structured Output

**Problem:** `CliReport.content` is currently a formatted text blob (see §2.1
example). This is fine for a terminal but bad for MCP — Claude Code would
have to re-parse text to extract structured facts (rule IDs, file
locations, severity), which is fragile and defeats the purpose of a
structured tool call.

**Needed:** Before or alongside MCP wiring, `CliCommands.guardrails()` and
`.decide()` should also return the underlying structured objects, not just
formatted text. The real objects already exist and are fully typed:

- `GuardrailViolation` (`packages/arch-guardrails/src/arch_guardrails/types.py`):
  ```python
  @dataclass
  class GuardrailViolation:
      rule_id: str          # e.g. "layer_boundaries", "dependency_direction", "module_sizing"
      severity: str          # "error" | "warning"
      location: str          # e.g. "core → types" or a module name
      message: str
      suggested_fix: str
      evidence: list[str] = field(default_factory=list)
  ```

- `Decision` / `Recommendation` (`packages/decision-engine/src/decision_engine/types.py`):
  ```python
  @dataclass
  class Recommendation:
      title: str
      description: str
      source: str            # "arch_guardrails" | "change_planner" | "feature_planner" | "refactoring_advisor"
      effort: str             # "low" | "medium" | "high"
      risk: str               # "low" | "medium" | "high"
      confidence: float       # 0.0-1.0
      suggested_fix: str
      evidence: list[str] = field(default_factory=list)

  @dataclass
  class Decision:
      intent: str
      options: list[Recommendation]
      recommended_option: Recommendation
      reasoning: str
      confidence: float
  ```

- `ImpactPrediction` (`packages/change-planner/src/change_planner/types.py`):
  ```python
  @dataclass
  class ImpactPrediction:
      changed_file: str
      affected_modules: list[str]
      affected_functions: list[str]
      cascade_risk: str       # "low" | "medium" | "high"
      confidence: float
      reasoning: str
      evidence: list[ImpactEdge]
  ```

**Recommendation for the MCP tool's actual JSON response shape** (once this
change lands), so both of you build against the same target:

```json
{
  "success": true,
  "title": "Architecture Check: repos/click",
  "summary": "Scanned 76 file(s). 2 violation(s) found.",
  "violations": [
    {
      "rule_id": "module_sizing",
      "severity": "warning",
      "location": "core",
      "message": "Module exceeds 500 lines (3681)",
      "suggested_fix": "Split into focused modules",
      "evidence": []
    }
  ]
}
```
for `ortho_guardrails`, and
```json
{
  "success": true,
  "intent": "add caching",
  "recommended": {
    "title": "...",
    "description": "...",
    "source": "arch_guardrails",
    "effort": "medium",
    "risk": "high",
    "confidence": 1.0,
    "suggested_fix": "...",
    "evidence": []
  },
  "alternatives": [ /* same Recommendation shape */ ],
  "reasoning": "..."
}
```
for `ortho_decide`.

**Action item:** this JSON-shape addition to `CliCommands` is a small,
scoped follow-up (add a method or parameter that returns structured data
alongside/instead of the text `CliReport`) — flag to me if you want it
built before your friend starts, or your friend's MCP server can call the
underlying `ArchitectureEnforcer`/`DecisionEngine` objects directly instead
of going through `CliCommands` at all (see §5 architecture note).

---

## 5. Known Constraints (must handle in MCP server)

1. **No unbounded cwd scans.** If `path`/`scan_path` is omitted, ortho
   scans cwd. In a large monorepo (this one included — `repos/` alone has
   7,882 vendored Python files) this can take 60+ seconds, violating the
   <2s MCP latency target. **MCP server should either require an explicit
   path from the calling context (e.g. the workspace root Claude Code is
   operating in) or apply its own stricter file-count/size guard before
   calling into ortho.**
2. **Empty/whitespace intent must be rejected client-side too** — don't
   rely solely on ortho's own check; fail fast in the MCP layer if
   possible to avoid a wasted round trip.
3. **`decide()` with a text intent and no `scan_path`** falls back to
   scanning `.` — same unbounded-scan risk as above. Always pass
   `scan_path` explicitly from MCP.
4. **Layer-boundary noise is largely fixed** (task-018, 2026-07-15):
   test/example/vendor directories are now excluded from layer detection,
   which eliminated the dominant false-positive pattern (measured 83 → 7
   violations on `repos/click`, a 92% reduction). A smaller residual
   pattern remains (production leaf/utility modules like `typing.py`
   occasionally mislabeled "Data layer") — still worth a severity
   distinction in the UI, but the volume problem is solved.

---

## 6. Architecture Layer Reference (for context, not required reading to integrate)

Per `.ases/architecture/adrs/ADR-015-layer-boundaries.md` and
`ADR-016-engineering-copilot-layer.md`:

```
apps/* (Claude Code, MCP server lives here or calls into this layer)
    ↓
packages/cli-commands  (Apps layer — orchestrates everything below)
    ↓
change-planner, arch-guardrails, decision-engine  (Engineering Copilot layer)
    ↓
repo-intelligence, arch-intelligence  (Intelligence layer)
```

The MCP server should call `packages/cli-commands`'s `CliCommands` class
(or the structured-output variant proposed in §4) — it should never import
directly from `repo-intelligence`/`arch-intelligence`/`arch-guardrails`
itself, to keep one clean integration seam.

---

## 7. Quick-Start for Your Friend

1. Confirm Python environment can import `cli_commands` (the package is at
   `packages/cli-commands/src/cli_commands/`, installed via the monorepo's
   existing Poetry/pip setup — same environment this doc's author used to
   verify all of the above).
2. Start with `ortho_guardrails` — still the most battle-tested path
   (100 passing tests as of 2026-07-15, `packages/cli-commands/tests/`),
   then add the other three; all four are real now.
3. Test against `repos/click` (already cloned in this monorepo,
   `repos/click/src/click`) — a real, small, known-good fixture confirmed
   to scan in ~2 seconds.
4. All four tools (`guardrails`, `decide`, `plan`, `refactor`) are safe
   to wrap as of task-019/020 (§2, §3).
5. Flag back to this doc's author (or open an issue) if `CliReport`'s
   text-only output blocks progress — the structured-output change (§4) is
   small and can be prioritized.
