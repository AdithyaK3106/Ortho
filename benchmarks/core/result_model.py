"""Canonical result shapes every suite returns.

Every suite's `evaluate()` returns a `SuiteResult`; `core/reports.py` renders
`list[SuiteResult]` to JSON/Markdown/CSV without any suite-specific code.
"""

from dataclasses import dataclass, field


@dataclass
class RunMetadata:
    """Reproducibility metadata attached to every SuiteResult in a run."""

    benchmark_version: str
    dataset_version: str  # manifest schema_version + pinned commit, joined
    adapter_version: str  # ortho_commit() or equivalent for a future adapter
    timestamp: str
    python_version: str
    platform: str  # sys.platform / platform.platform()
    config: dict


@dataclass
class SuiteResult:
    """Canonical output of one suite's evaluate() call against one dataset."""

    suite: str
    dataset: str
    metrics: dict[str, float] = field(default_factory=dict)
    detail: dict = field(default_factory=dict)
    timings: dict[str, float] = field(default_factory=dict)
    status: str = "SUCCESS"  # SUCCESS | FAILED | PARTIAL
    error: str | None = None
    run_metadata: RunMetadata | None = None
