"""Pytest path bootstrap: put benchmarks/ on sys.path so `core.*`, `adapters.*`,
`suites.*`, `validation.*` import as top-level packages (matching run_benchmark.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
