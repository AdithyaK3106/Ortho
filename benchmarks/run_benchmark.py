"""Ortho engineering benchmark runner -- thin CLI.

Usage:
    python benchmarks/run_benchmark.py                       # all suites, all datasets
    python benchmarks/run_benchmark.py --only flask           # one dataset
    python benchmarks/run_benchmark.py --suites repository,architecture

Builds a `BenchmarkConfig` from CLI args, discovers datasets under
`--datasets-dir` (each needing a `manifest.json`), runs each requested suite's
`evaluate(adapter, dataset_item, config)` via `core.runner.run_suite`, and
renders `list[SuiteResult]` through `core.reports` (JSON + Markdown + CSV).

No per-suite CLI, no standalone `cli/` package (YAGNI at 5 suites / 2 datasets
-- see plan.md's explicit out-of-scope list).
"""

import argparse
import importlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import BenchmarkConfig
from core.ground_truth import load_manifest, GroundTruthError
from core.reports import to_csv, to_json, to_markdown
from core.result_model import RunMetadata
from core.runner import ROOT, run_suite
from adapters.ortho.adapter import OrthoAdapter

BENCHMARK_VERSION = "0.1.0"

ALL_SUITES = ("repository", "architecture", "impact", "efficiency", "retrieval")


def ortho_commit() -> str:
    """Reused unchanged from pre-refactor run_benchmark.py."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def discover_datasets(datasets_dir: Path, only: list[str] | None) -> list[dict]:
    """Find every subdirectory of datasets_dir with a manifest.json."""
    items = []
    for d in sorted(datasets_dir.iterdir()):
        if not d.is_dir():
            continue
        if only and d.name not in only:
            continue
        manifest_path = d / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = load_manifest(d)
        items.append({
            "name": d.name,
            "dataset_dir": d,
            "repo_path": ROOT / "repos" / manifest["repo"],
            "manifest": manifest,
        })
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the Ortho engineering benchmark suite.")
    ap.add_argument("--datasets-dir", type=Path,
                     default=Path(__file__).parent / "datasets")
    ap.add_argument("--output-dir", type=Path,
                     default=Path(__file__).parent / "results")
    ap.add_argument("--budget", type=int, default=8000, help="Context token budget")
    ap.add_argument("--retrieval-k", default="5,10",
                     help="Comma-separated k values for retrieval metrics")
    ap.add_argument("--only", default="",
                     help="Comma-separated dataset names to run (subset)")
    ap.add_argument("--suites", default=",".join(ALL_SUITES),
                     help="Comma-separated suite names to run")
    args = ap.parse_args()

    only = [n.strip() for n in args.only.split(",") if n.strip()] or None
    retrieval_k = tuple(int(k) for k in args.retrieval_k.split(",") if k.strip())
    suite_names = [s.strip() for s in args.suites.split(",") if s.strip()]

    config = BenchmarkConfig(
        datasets_dir=args.datasets_dir,
        output_dir=args.output_dir,
        token_budget=args.budget,
        retrieval_k=retrieval_k,
        only=only,
    )

    try:
        dataset_items = discover_datasets(config.datasets_dir, config.only)
    except GroundTruthError as e:
        print(f"ERROR: {e}")
        return 1
    if not dataset_items:
        print("No datasets found.")
        return 1

    adapter = OrthoAdapter()
    run_metadata = RunMetadata(
        benchmark_version=BENCHMARK_VERSION,
        dataset_version="",  # filled per-result below (per dataset manifest)
        adapter_version=ortho_commit(),
        timestamp=datetime.now(timezone.utc).isoformat(),
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        config={"token_budget": config.token_budget, "retrieval_k": list(config.retrieval_k),
                "only": config.only},
    )

    all_results = []
    for suite_name in suite_names:
        try:
            suite_module = importlib.import_module(f"suites.{suite_name}.evaluate")
        except ImportError as e:
            print(f"WARNING: suite '{suite_name}' could not be imported: {e}")
            continue

        print(f"[{suite_name}] running against {len(dataset_items)} dataset(s)")
        results = run_suite(suite_module, adapter, dataset_items, config)
        for r in results:
            manifest = next((d["manifest"] for d in dataset_items if d["name"] == r.dataset), {})
            r.run_metadata = RunMetadata(
                benchmark_version=run_metadata.benchmark_version,
                dataset_version=f"{manifest.get('schema_version', '?')}@{manifest.get('commit', '?')}",
                adapter_version=run_metadata.adapter_version,
                timestamp=run_metadata.timestamp,
                python_version=run_metadata.python_version,
                platform=run_metadata.platform,
                config=run_metadata.config,
            )
        all_results.extend(results)
        for r in results:
            print(f"  {r.dataset}: {r.status} {r.metrics}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = config.output_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(to_json(all_results), encoding="utf-8")
    (out_dir / "results.csv").write_text(to_csv(all_results), encoding="utf-8")
    (out_dir / "report.md").write_text(to_markdown(all_results), encoding="utf-8")

    ok = sum(1 for r in all_results if r.status == "SUCCESS")
    print("=" * 70)
    print(f"Done: {ok}/{len(all_results)} suite runs succeeded")
    print(f"Reports: {out_dir}")
    return 0 if ok == len(all_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
