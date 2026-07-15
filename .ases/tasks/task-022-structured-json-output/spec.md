# Spec — task-022-structured-json-output

## CliReport Type Extension

**File:** `packages/cli-commands/src/cli_commands/types.py`

```python
from dataclasses import dataclass, field
from typing import Optional

# Import the real structured types
from arch_guardrails.types import GuardrailViolation
from decision_engine.types import Recommendation

@dataclass
class CliReport:
    title: str
    content: str
    format: str = "text"
    success: bool = True
    # NEW: optional structured output
    violations: Optional[list[GuardrailViolation]] = None
    recommendations: Optional[list[Recommendation]] = None
```

Both new fields default to `None`, preserving backward compatibility.

## guardrails() Implementation

```python
def guardrails(self, path: str | None = None, **kwargs: Any) -> CliReport:
    # ... existing scan/enforcer logic ...
    violations = enforcer.check_violations()  # Already exists
    
    # Format to text (unchanged)
    if not violations:
        content = f"Scanned {len(scan.file_to_module)} file(s). No violations found."
    else:
        lines = [
            f"[{v.severity}] {v.rule_id} at {v.location}: {v.message} -> {v.suggested_fix}"
            for v in violations
        ]
        content = "\n".join(lines)
    
    report = CliReport(
        title=f"Architecture Check: {target}",
        content=content,
        success=True,
        violations=violations  # NEW: assign real objects
    )
    capture_workflow_run(target, "guardrails", target, report)
    return report
```

**Key:** capture the `violations` list before formatting, assign it to 
`report.violations`.

## decide() Implementation

```python
def decide(self, intent: str, **kwargs: Any) -> CliReport:
    # ... existing scan/predictor/enforcer logic ...
    decision = engine.decide(...)  # Already exists, returns Decision object
    
    # Format to text (unchanged)
    alt_titles = [opt.title for opt in decision.options if opt is not decision.recommended_option]
    content = f"Decision for: {intent}\n\nRecommended: {decision.recommended_option.title}\n{decision.reasoning}"
    if alt_titles:
        content += f"\nAlternatives: {', '.join(alt_titles)}"
    
    report = CliReport(
        title=f"Decision: {intent}",
        content=content,
        success=True,
        recommendations=decision.options  # NEW: assign all options (recommended + alternatives)
    )
    capture_workflow_run(scan_target, "decide", intent, report)
    return report
```

**Key:** assign `decision.options` (which includes both the recommended 
option and all alternatives) to `report.recommendations`.

## Text Output (Unchanged)

The `content` field must remain **identical** to pre-task output. If 
existing tests assert the exact text of a guardrails or decide output, 
those assertions must still pass without modification.

## Backward Compatibility

- Existing Python callers that access only `report.title`, `report.content`, 
  `report.success` are unaffected.
- The new fields are optional (`None` by default) — JSON serialization 
  libraries can omit them or include them as `null`.
- CLI output (copilot.ts/copilot.py) is unaffected — they only print 
  `report.content`.

## Real-Repo Verification

Running guardrails/decide against `repos/click`:

```python
report = CliCommands().guardrails("repos/click")
assert report.violations is not None
assert len(report.violations) > 0
assert all(isinstance(v, GuardrailViolation) for v in report.violations)
assert all(v.rule_id in ["layer_boundaries", "circular_dependencies", "module_sizing"] 
           for v in report.violations)
```

```python
report = CliCommands().decide("add caching", scan_path="repos/click")
assert report.recommendations is not None
assert len(report.recommendations) > 0
assert all(isinstance(r, Recommendation) for r in report.recommendations)
```

## MCP Contract Update

Appendix added to `docs/mcp-server-contract.md` documenting the new 
structured shape for MCP tool responses (informational only; no code changes 
to the bridge).
