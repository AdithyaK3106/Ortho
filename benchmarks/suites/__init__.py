"""Benchmark suites: each `suites/<name>/evaluate.py` exposes
`evaluate(adapter, dataset_item, config) -> SuiteResult`.

No suite imports from `packages/*` directly -- only through the adapter.
"""
