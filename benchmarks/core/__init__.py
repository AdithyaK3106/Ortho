"""Vendor-neutral core: config, result model, runner, ground truth, reports, metrics.

No file in this package may import from `packages/*` (Ortho internals). Only
`adapters/ortho/adapter.py` is allowed to do that — see
`validation/test_adapter_contract.py` and the import-boundary check.
"""
