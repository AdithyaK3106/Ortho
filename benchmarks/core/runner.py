"""Vendor-agnostic runner primitives: clone, failure classification, stage timing,
and the generic per-suite execution loop.

`clone_repo`, `PipelineFailure`, and the `timed()` stage-timing pattern are moved
unchanged from the pre-refactor `benchmarks/pipeline.py` (task-015). No suite
logic lives here -- only orchestration plumbing shared by every suite.
"""

import subprocess
import time
from pathlib import Path

from core.result_model import SuiteResult

ROOT = Path(__file__).resolve().parents[2]
CLONE_TIMEOUT_SEC = 900


class PipelineFailure(Exception):
    """A classified benchmark stage failure (category + message)."""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


def _fail(category: str):
    """Decorator-ish helper: wrap a stage callable, classify its exceptions."""

    def wrap(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PipelineFailure:
            raise
        except Exception as e:  # noqa: BLE001 - classification boundary
            raise PipelineFailure(category, f"{type(e).__name__}: {e}") from e

    return wrap


def timed(timings: dict, stage: str, category: str, fn, *args, **kwargs):
    """Run fn(*args, **kwargs), classify failures under `category`, record duration."""
    t0 = time.perf_counter()
    try:
        return _fail(category)(fn, *args, **kwargs)
    finally:
        timings[stage] = round(time.perf_counter() - t0, 3)


def clone_repo(url: str, dest: Path) -> str:
    """Clone from GitHub (shallow) unless already present. Returns 'cloned'|'cached'."""
    if dest.exists() and any(dest.iterdir()):
        return "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", "--single-branch", url, str(dest)],
        capture_output=True, text=True, timeout=CLONE_TIMEOUT_SEC,
    )
    if proc.returncode != 0:
        raise PipelineFailure("clone", f"git clone failed: {proc.stderr.strip()[:400]}")
    return "cloned"


def run_suite(suite_module, adapter, dataset_items: list[dict], config) -> list[SuiteResult]:
    """Run one suite module's evaluate() against every dataset item.

    `suite_module` must expose `evaluate(adapter, dataset_item, config) -> SuiteResult`.
    Never raises: a suite exception becomes a FAILED SuiteResult so one bad
    dataset item doesn't abort the whole run.
    """
    results: list[SuiteResult] = []
    for item in dataset_items:
        try:
            results.append(suite_module.evaluate(adapter, item, config))
        except Exception as e:  # noqa: BLE001 - suite-level failure boundary
            results.append(SuiteResult(
                suite=getattr(suite_module, "SUITE_NAME", suite_module.__name__),
                dataset=item.get("name", "unknown"),
                status="FAILED",
                error=f"{type(e).__name__}: {e}",
            ))
    return results
