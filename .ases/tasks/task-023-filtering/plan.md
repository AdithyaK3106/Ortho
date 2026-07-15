# Plan — task-023-filtering

## Goal
Pilots want to filter noise: "show me only high-severity violations" or 
"show me only high-confidence recommendations." Add severity and confidence 
filtering to both Python API and CLI, so users can focus on high-impact 
findings and reduce decision fatigue.

## Current State
- `guardrails()` returns all violations (mix of `error` and `warning` severity)
  on real repos like click, this is 7–20 findings. Pilots want "errors only" 
  mode.
- `decide()` returns all recommendations (typically 2–5 options with varying 
  confidence scores). Pilots want "high-confidence only" filtering.
- No filtering at all today — CLI prints full list, Python API returns 
  full list.

## Scope

### Python API: CliCommands method signatures (backward-compatible)
Add optional parameters:
```python
def guardrails(self, path: str | None = None, 
               severity_filter: str | None = None,  # "error" | "warning" or None
               **kwargs: Any) -> CliReport:
    ...

def decide(self, intent: str, 
           confidence_threshold: float | None = None,  # 0.0–1.0 or None
           **kwargs: Any) -> CliReport:
    ...
```

Both default to `None` (no filtering, return all). When provided, filter the 
violations/recommendations BEFORE formatting to text and BEFORE assigning to 
`report.violations`/`report.recommendations`.

### CLI: copilot.ts and copilot.py bridge
Add optional flags:
```
ortho guardrails [path] [--severity error|warning]
ortho decide <intent> [--scan-path] [--confidence 0.0-1.0]
```

Pass through to the Python methods via kwargs. TS-side validation: 
`--severity` must be "error" or "warning" (enum), `--confidence` must be 
a float 0.0–1.0 (range check).

### Text Output Impact
The `content` field (formatted text) **changes** when filtering is applied:
- `guardrails` with `--severity error` shows only error violations 
  (warnings filtered out of text).
- `decide` with `--confidence 0.8` shows only recommendations with confidence 
  >= 0.8.
- Summary line should reflect filtering: "Scanned N file(s). K violations 
  found (M filtered by severity)."

### Structured Output Impact
Both `report.violations` and `report.recommendations` contain **only** the 
filtered subset. The raw, unfiltered violations/recommendations are NOT 
available once a filter is applied (design tradeoff: simpler than dual lists).

## Acceptance Criteria
1. `guardrails(path, severity_filter="error")` returns only error violations 
   in both structured (`report.violations`) and text (`report.content`) output.
2. `guardrails(path, severity_filter="warning")` returns only warning violations.
3. `guardrails(path, severity_filter=None)` returns all violations (default).
4. `decide(intent, confidence_threshold=0.8)` returns only recommendations 
   with confidence >= 0.8.
5. `decide(intent, confidence_threshold=None)` returns all recommendations.
6. CLI `ortho guardrails --severity error` invokes `guardrails(path, 
   severity_filter="error")`.
7. CLI `ortho decide "..." --confidence 0.8` invokes `decide(intent, 
   confidence_threshold=0.8)`.
8. TS-side validation: invalid `--severity` or `--confidence` are caught 
   before spawn (exit 1 with a clear error message).
9. Text content reflects filtering (e.g., summary line shows filtered count).
10. All existing 126 tests still pass (backward compatibility: default 
    behavior unchanged).
11. New tests verify filtering behavior on real repos.
