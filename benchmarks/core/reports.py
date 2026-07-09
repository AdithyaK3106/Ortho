"""Suite-agnostic reporting: JSON, Markdown, CSV over `list[SuiteResult]`.

Pure functions. No suite name is ever special-cased -- metrics/detail keys
are whatever the suite produced, rendered generically.
"""

import csv
import io
import json
from dataclasses import asdict

from core.result_model import SuiteResult


def to_json(results: list[SuiteResult]) -> str:
    """Serialize results to a JSON array of SuiteResult dicts."""
    return json.dumps([asdict(r) for r in results], indent=2, default=str)


def to_markdown(results: list[SuiteResult]) -> str:
    """Render results as a Markdown report: one summary table + per-result detail."""
    lines = ["# Benchmark Results", ""]

    ok = [r for r in results if r.status == "SUCCESS"]
    other = [r for r in results if r.status != "SUCCESS"]
    lines.append(f"- **Total:** {len(results)} ({len(ok)} SUCCESS, {len(other)} other)")
    lines.append("")

    lines += ["## Summary", "", "| Suite | Dataset | Status | Metrics |", "|---|---|---|---|"]
    for r in results:
        metrics_str = ", ".join(f"{k}={v}" for k, v in sorted(r.metrics.items()))
        lines.append(f"| {r.suite} | {r.dataset} | {r.status} | {metrics_str} |")
    lines.append("")

    for r in results:
        lines += [f"## {r.suite} / {r.dataset}", "", f"**Status:** {r.status}"]
        if r.error:
            lines.append(f"**Error:** `{r.error}`")
        if r.metrics:
            lines += ["", "**Metrics:**", ""]
            lines += [f"- {k}: {v}" for k, v in sorted(r.metrics.items())]
        if r.timings:
            lines += ["", "**Timings (s):**", ""]
            lines += [f"- {k}: {v}" for k, v in sorted(r.timings.items())]
        if r.detail:
            lines += ["", "**Detail:**", "", "```json", json.dumps(r.detail, indent=2, default=str), "```"]
        lines.append("")

    return "\n".join(lines) + "\n"


def to_csv(results: list[SuiteResult]) -> str:
    """Render results as CSV: one row per SuiteResult, one column per distinct metric.

    Columns are the union of all metric keys across all results (sorted),
    plus suite/dataset/status/error. Missing metrics for a given result are
    left blank. No suite-specific columns.
    """
    all_metric_keys = sorted({k for r in results for k in r.metrics})
    fieldnames = ["suite", "dataset", "status", "error"] + all_metric_keys

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        row = {"suite": r.suite, "dataset": r.dataset, "status": r.status,
               "error": r.error or ""}
        row.update({k: r.metrics.get(k, "") for k in all_metric_keys})
        writer.writerow(row)
    return buf.getvalue()
