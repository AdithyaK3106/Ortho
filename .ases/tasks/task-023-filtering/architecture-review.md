# Architecture Review — task-023-filtering

**Verdict:** APPROVED

## Design Analysis

### API Extension Pattern
Adding optional `severity_filter` and `confidence_threshold` parameters to 
`CliCommands.guardrails()` and `.decide()` follows the existing pattern 
established in task-021 (`scan_path` kwarg): opt-in, backward-compatible 
parameter expansion. Default `None` means no filtering (preserve existing 
behavior). No new classes, no new dependencies, no architectural shifts.

### Filtering Semantics
**guardrails():** Simple list comprehension filtering on an already-computed 
violations list (before formatting). Severity is a string enum ("error" or 
"warning") — exact-match filtering is correct and efficient.

**decide():** Filters recommendation options on confidence score (float 0.0–1.0, 
threshold-based comparison). One edge case: if all recommendations fall below 
the threshold, spec says "pick the highest-confidence option as recommended and 
note the filtering in text" — reasonable fallback to always show *something* 
rather than empty output.

### Backward Compatibility
- Existing callers passing no filter parameters see identical behavior.
- Existing tests (126/126) verify default paths, should pass unmodified.
- Text output changes only when filtering is applied (summary line reflects 
  filter counts) — existing non-filtered output is identical to today.
- Structured output (violations/recommendations fields) contains only the 
  filtered subset — callers expecting the full list must explicitly request 
  it by not passing filter params.

### CLI/Bridge Validation
**TS-side validation (copilot.ts):** Catches invalid `--severity` and 
`--confidence` values before spawn, exits 1 with a clear error message. 
Avoids wasted subprocess round-trips for bad input.

**Python-side validation (copilot.py):** Argparse handles enum/range validation 
as a defense-in-depth layer. Matches the pattern used elsewhere in the CLI 
(context.py style).

### No New ADRs Required
Filtering is a presentation-layer feature, not an architectural decision. 
No new layers, no new dependencies, no new integration seams. Stays entirely 
within the Apps layer (CliCommands + CLI bridge).

## Correctness Checks

1. **What if confidence_threshold is exactly 0.0 or 1.0?**
   Both are valid (inclusive range: `>= 0.0`, `<= 1.0`). A recommendation 
   with confidence 0.8 passes threshold 0.8. Correct.

2. **What if severity_filter is provided but all violations match?**
   Returns all violations, text says "K violations found (0 filtered)" — correct.

3. **What if decide() filtering removes all but one option?**
   Returns the single remaining option with text noting it's the only one above 
   threshold. Correct.

4. **Performance impact?**
   List comprehensions over typically 7–20 violations or 2–5 recommendations 
   are O(n) with small n. Negligible.

5. **Does filtering interact safely with task-020 workflow capture?**
   Capture happens after filtering (after report.violations/recommendations 
   are set). Workflow_run artifact stores the text content, which already 
   reflects the filtering in the summary line. No conflict.

## Verdict
**APPROVED** — purely additive, backward-compatible, no new ADRs needed. 
Filtering is a sensible presentation-layer feature that pilots will appreciate.
