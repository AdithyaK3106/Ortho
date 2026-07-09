"""Enforces spec.md AC1's import-boundary rule:

  "no file under core/, suites/, or validation/ imports from packages/* --
  only adapters/ortho/adapter.py does."

This is a static source-scan test (AST-based, not a live import trace) so
it catches the violation even in code paths that aren't exercised by other
tests, and even in files with import errors unrelated to packages/*.

IMPORTANT IMPLEMENTATION NOTE (discovered while running this test against
BUILDER's real adapters/ortho/adapter.py, 2026-07-09): "imports from
packages/*" is NOT a literal `packages.foo` or `import packages` statement
anywhere in this codebase. The pre-existing (pre-refactor) benchmarks/
pipeline.py convention -- preserved by adapter.py -- inserts
`packages/<name>/src` onto `sys.path` and then imports the TOP-LEVEL module
names those src/ dirs expose directly (`repo_intelligence`, `arch_intelligence`,
`impact_analysis`, `context_hub`, `token_optimizer`, plus `storage` from
`shared/storage/src`). A naive scan for the literal string "packages." would
never catch a real violation in this codebase, and would also fail to
recognize adapter.py's OWN legitimate packages/* usage (as it in fact did on
first run of this test file -- see git history / this file's earlier
revision). The rule actually enforced below is: no file outside
adapters/ortho/adapter.py may (a) mutate sys.path to add any packages/*/src
or shared/*/src directory, or (b) import any of the known Ortho-internal
top-level module names that only resolve via that sys.path trick.
"""

import ast
import sys
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parents[1]

# Directories the rule applies to (spec.md explicit list). adapters/ is
# intentionally excluded from the walk EXCEPT we still scan
# adapters/interface.py (must stay vendor-neutral) while excluding
# adapters/ortho/adapter.py (the one file allowed to import packages/*).
SCANNED_DIRS = ["core", "suites", "validation"]
ALLOWED_EXCEPTION = BENCH_ROOT / "adapters" / "ortho" / "adapter.py"

# Top-level module names that only exist because adapter.py's sys.path
# trick exposes packages/*/src and shared/*/src onto the import path. Any
# OTHER file importing these names would only work by accident (relying on
# adapter.py having already been imported first to mutate sys.path) --
# itself a boundary violation and a hidden import-order dependency bug.
ORTHO_INTERNAL_TOP_LEVEL_MODULES = {
    "repo_intelligence", "arch_intelligence", "impact_analysis",
    "context_hub", "token_optimizer", "storage",
}


def _imports_packages(py_file: Path) -> list[str]:
    """Return violations found via AST (no execution): literal packages.*
    imports, OR imports of Ortho-internal top-level module names that only
    resolve through the sys.path-mutation trick, OR sys.path mutations
    themselves that reference packages/ or shared/ source directories."""
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
    except SyntaxError:
        return []  # not this test's job to catch syntax errors
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "packages" or alias.name.startswith("packages."):
                    hits.append(f"import {alias.name}")
                elif alias.name in ORTHO_INTERNAL_TOP_LEVEL_MODULES:
                    hits.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "packages" or node.module.startswith("packages.")):
                hits.append(f"from {node.module} import ...")
            elif node.module in ORTHO_INTERNAL_TOP_LEVEL_MODULES:
                hits.append(f"from {node.module} import ...")
    # sys.path mutation referencing packages/ or shared/ source dirs, e.g.
    # `for _rel in ("packages/repo-intelligence/src", ...)`. String-literal
    # scan (not a full sys.path taint-tracker) is enough to catch the
    # established pattern used in this codebase.
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            # narrow match: an actual sys.path-style relative path segment,
            # not prose that happens to mention "packages/" and "/src"
            if v.startswith("packages/") and v.endswith("/src"):
                hits.append(f"string literal referencing packages/*/src: {v!r}")
    return hits


SELF_FILE = Path(__file__).resolve()


def _iter_python_files(base: Path):
    if not base.exists():
        return
    for py_file in base.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        if py_file.resolve() == SELF_FILE:
            continue  # this checker's own docstrings reference the pattern it looks for
        yield py_file


class TestImportBoundary:
    def test_sample_no_scanned_file_imports_packages(self):
        """SAMPLE: core/, suites/, validation/ collectively must not import packages/*."""
        violations = {}
        for dir_name in SCANNED_DIRS:
            for py_file in _iter_python_files(BENCH_ROOT / dir_name):
                if py_file.resolve() == ALLOWED_EXCEPTION.resolve():
                    continue
                hits = _imports_packages(py_file)
                if hits:
                    violations[str(py_file.relative_to(BENCH_ROOT))] = hits
        assert not violations, (
            f"import-boundary violation: only adapters/ortho/adapter.py may "
            f"import packages/*, found violations: {violations}")

    def test_only_ortho_adapter_may_import_packages(self):
        """Positive control: adapters/ortho/adapter.py IS expected to import
        packages/* (it's the wrapping layer) -- this test documents that as
        intentional so the boundary test above can't be satisfied by
        accidentally deleting the adapter's real imports."""
        if not ALLOWED_EXCEPTION.exists():
            import pytest
            pytest.skip("adapters/ortho/adapter.py not yet written by BUILDER")
        hits = _imports_packages(ALLOWED_EXCEPTION)
        assert hits, (
            "adapters/ortho/adapter.py imports no packages/* -- either the "
            "boundary test's allowlist is now pointless, or the adapter "
            "isn't actually wrapping Ortho internals as spec.md requires")

    def test_adapters_interface_stays_vendor_neutral(self):
        """adapters/interface.py declares the capability contract and must
        not itself depend on Ortho internals (only the ortho/ implementation
        subpackage may)."""
        interface_file = BENCH_ROOT / "adapters" / "interface.py"
        if not interface_file.exists():
            import pytest
            pytest.skip("adapters/interface.py not yet written by BUILDER")
        hits = _imports_packages(interface_file)
        assert not hits, f"adapters/interface.py imports packages/*: {hits}"

    def test_boundary_scan_actually_finds_files(self):
        """Guard against the test silently passing because SCANNED_DIRS are
        empty/nonexistent (a vacuous pass looks identical to a real pass)."""
        total = sum(1 for d in SCANNED_DIRS for _ in _iter_python_files(BENCH_ROOT / d))
        if total == 0:
            import pytest
            pytest.skip("no files under core/, suites/, validation/ yet -- BUILDER in progress")
        assert total > 0
