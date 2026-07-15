# Spec — task-023-filtering

## Python API: Filtering Semantics

### guardrails()

```python
def guardrails(self, path: str | None = None, 
               severity_filter: str | None = None,
               **kwargs: Any) -> CliReport:
```

**severity_filter parameter:**
- `None` (default): return all violations
- `"error"`: return only violations where `v.severity == "error"`
- `"warning"`: return only violations where `v.severity == "warning"`
- Any other value: raise `ValueError`

**Behavior:**
1. Call `ArchitectureEnforcer.check_violations()` as usual.
2. If `severity_filter` is not None, filter the violations list:
   ```python
   violations = [v for v in violations if v.severity == severity_filter]
   ```
3. Format to text (violations list, now filtered).
4. Assign filtered violations to `report.violations`.
5. Text summary line should indicate filtering:
   - If all violations shown (no filter): "Scanned N file(s). K violations found."
   - If filtered: "Scanned N file(s). K violations found (M filtered by severity)."

### decide()

```python
def decide(self, intent: str,
           confidence_threshold: float | None = None,
           **kwargs: Any) -> CliReport:
```

**confidence_threshold parameter:**
- `None` (default): return all recommendations
- `0.0–1.0`: return only recommendations where `r.confidence >= threshold`
- Any value outside [0.0, 1.0]: raise `ValueError`

**Behavior:**
1. Call `DecisionEngine.decide()` as usual.
2. If `confidence_threshold` is not None, filter the options:
   ```python
   options = [r for r in decision.options if r.confidence >= confidence_threshold]
   ```
3. If filtering results in zero options (all filtered out), pick the 
   highest-confidence option as recommended and note "All recommendations 
   filtered; showing highest-confidence option."
4. Format to text (options list, now filtered).
5. Assign filtered options to `report.recommendations`.
6. Text summary should indicate filtering:
   - If all recommendations shown: "Recommended: <title>"
   - If filtered: "Recommended: <title> (highest-confidence; M recommendations filtered by confidence)"

## CLI: Bridge Signatures

### copilot.py

```
python copilot.py guardrails --path <dir> [--severity error|warning]
python copilot.py decide <intent> --scan-path <dir> [--confidence 0.0-1.0]
```

Pass arguments to CliCommands:
```python
if args.severity:
    if args.severity not in ["error", "warning"]:
        parser.error(f"--severity must be 'error' or 'warning', got '{args.severity}'")
    report = commands.guardrails(args.path, severity_filter=args.severity)
else:
    report = commands.guardrails(args.path)

if args.confidence is not None:
    try:
        conf = float(args.confidence)
        if not (0.0 <= conf <= 1.0):
            parser.error(f"--confidence must be 0.0–1.0, got {conf}")
    except ValueError:
        parser.error(f"--confidence must be a float, got '{args.confidence}'")
    report = commands.decide(args.intent, scan_path=args.scan_path, 
                             confidence_threshold=conf)
else:
    report = commands.decide(args.intent, scan_path=args.scan_path)
```

### copilot.ts

```typescript
guardrailsCommand
  .command("guardrails [path]")
  .option("--severity <level>", "error or warning (default: all)")
  .action(async (path?: string, options?: { severity?: string }) => {
    if (options?.severity && !["error", "warning"].includes(options.severity)) {
      console.error(`Error: --severity must be 'error' or 'warning', got '${options.severity}'`);
      process.exit(1);
    }
    const args = ["guardrails", "--path", path || process.cwd()];
    if (options?.severity) args.push("--severity", options.severity);
    await runCopilot(args);
  });

decideCommand
  .command("decide <intent>")
  .option("--scan-path <dir>", "Directory to scan")
  .option("--confidence <threshold>", "Minimum confidence 0.0–1.0")
  .action(async (intent: string, options?: { scanPath?: string; confidence?: string }) => {
    requireIntent(intent, "decide");
    if (options?.confidence) {
      const conf = parseFloat(options.confidence);
      if (isNaN(conf) || conf < 0.0 || conf > 1.0) {
        console.error(`Error: --confidence must be 0.0–1.0, got '${options.confidence}'`);
        process.exit(1);
      }
    }
    const args = ["decide", intent, "--scan-path", options?.scanPath || process.cwd()];
    if (options?.confidence) args.push("--confidence", options.confidence);
    await runCopilot(args);
  });
```

## Backward Compatibility

- Default behavior (no filtering) is unchanged: `guardrails()` returns all 
  violations, `decide()` returns all recommendations.
- Existing tests pass unmodified.
- CLI users who don't pass `--severity` or `--confidence` see no change.

## Real-Repo Verification

Example workflow:
```bash
# Show all guardrails violations (today's behavior)
ortho guardrails repos/click

# Show only errors (new)
ortho guardrails repos/click --severity error
# Output should have fewer violations, summary shows filter count

# Show only high-confidence recommendations (new)
ortho decide "add caching" --scan-path repos/click --confidence 0.8
# Output should show only recommendations with confidence >= 0.8
```
