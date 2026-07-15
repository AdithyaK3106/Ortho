# Architecture Review — task-022-structured-json-output

**Verdict:** APPROVED

## Design Analysis

### Type Safety & Imports
`CliReport` imports `GuardrailViolation` from `arch_guardrails.types` and 
`Recommendation` from `decision_engine.types`. Per ADR-016, 
`packages/cli-commands` (Apps layer) importing Engineering-Copilot-layer 
types (`arch_guardrails`, `decision_engine`) is exactly the established 
pattern: `CliCommands` already calls into these engines at runtime; 
importing their return types for type hints is the correct extension. No 
new architectural layers or circular dependencies.

### Backward Compatibility
Optional fields with `None` defaults preserve the existing API contract:
- Existing code reading `report.success` / `report.content` / `report.title` 
  sees no change.
- New code can opt-in to structured output: 
  `if report.violations: ...` — idiomatic Python, zero surprises.
- Text formatting is unchanged — the new fields are *shadows* of the 
  formatted content, not replacements.
- CLI commands (copilot.ts/copilot.py) print only `report.content`, so 
  `ortho guardrails` / `ortho decide` output is identical byte-for-byte.

### Implementation Fidelity to Spec
**guardrails():** The enforcer already calls `check_violations()` and has 
the real violations list before formatting. The task is to capture that 
list and assign it to `report.violations` — a one-line addition alongside 
the existing content formatting. Text output is unchanged (same format 
string as today).

**decide():** The decision engine already returns a `Decision` object with 
`options` (a list of `Recommendation` objects). The task is to extract 
that list and assign it to `report.recommendations` before formatting. 
Text output is unchanged (same format logic as today).

### No New ADRs Required
This task does not introduce new layers, new dependency directions, or 
architectural patterns. It is a type-safe extension of the existing 
`guardrails()` and `decide()` return types, purely additive.

### Integration Points
- **CliCommands callers** (e.g., MCP servers, future dashboards): can now 
  access structured findings via `report.violations` / 
  `report.recommendations` — machine-readable, no text parsing needed.
- **CLI layer** (copilot.ts/copilot.py): unchanged — they continue printing 
  `report.content` to stdout. The structured fields are invisible to the 
  terminal user.
- **ContextHub capture** (task-020): unchanged — workflow_run artifacts 
  store only the text content. Structured data can be added to future 
  artifact types, but not to workflow_run.
- **Tests**: existing 100/100 tests verify text output is preserved; new 
  tests verify structured fields are populated correctly.

### Correctness Checks
1. **Does `guardrails()` break if violations is None or empty?**
   No — the logic `if not violations: content = "Scanned..."` handles both 
   cases correctly. Assigning `violations=[]` (empty list) is safe and 
   idiomatic.

2. **Does `decide()` break if decision.options is empty?**
   No — the decision engine always returns at least the recommended option 
   (guaranteed by DecisionEngine contract), so options will never be empty.

3. **Can the text output accidentally change?**
   Only if the formatting logic is modified. Acceptance criteria #4 and 
   existing tests (#6) guard against this — any accidental text change 
   will surface as a test failure immediately.

4. **Is there a performance cost?**
   No — we're not doing additional work, only *keeping* the structured 
   objects that are already computed. A list reference assignment is O(1).

## Verdict
**APPROVED** — no ADR needed, purely additive, backward-compatible, 
correct by design. The implementation mirrors the existing pattern of 
`CliCommands` wrapping engine objects into reports.
