"""Central benchmark configuration, built once and passed to every suite."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BenchmarkConfig:
    """Configuration shared by every suite's `evaluate(adapter, dataset_item, config)`.

    Built once in `run_benchmark.py` from CLI args -- no per-suite argparse.
    """

    datasets_dir: Path
    output_dir: Path
    token_budget: int = 8000
    retrieval_k: tuple[int, ...] = field(default_factory=lambda: (5, 10))
    only: list[str] | None = None
