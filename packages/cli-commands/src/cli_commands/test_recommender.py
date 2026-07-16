"""Test Intelligence: recommend real test files for a set of affected modules.

Never invents a test file name. Only reports test files that actually exist
on disk in the scanned repo, discovered via pytest's own naming
conventions (test_<name>.py / <name>_test.py, either alongside the module
or under a tests/ directory). A module with no discoverable test file is
reported as a coverage gap, not silently skipped -- the roadmap's "never
fabricate, say I don't know when uncertain" applies here as "never invent
a test file name that might not exist."
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TestRecommendation:
    affected_module: str
    test_modules: list[str] = field(default_factory=list)
    has_coverage: bool = False


def _test_name_candidates(module_stem: str) -> set[str]:
    return {f"test_{module_stem}", f"{module_stem}_test"}


def recommend_tests(
    affected_modules: list[str],
    file_to_module: dict[str, str],
) -> list[TestRecommendation]:
    """For each affected module, find real test modules already present in
    the scan (file_to_module's own keys), matched by pytest naming
    convention. Distinct from the module itself, so a module named
    test_foo.py doesn't recommend itself as its own test.

    Entries in affected_modules may be either dotted module names or raw
    file paths (upstream callers -- e.g. ChangePredictor's
    ImpactPrediction.affected_modules -- are inconsistent about which),
    so each entry is resolved through file_to_module first if it matches a
    known file path, falling back to treating it as a module name already."""
    all_modules = set(file_to_module.values())

    recommendations: list[TestRecommendation] = []
    for entry in affected_modules:
        module = file_to_module.get(entry, entry)
        stem = module.rsplit(".", 1)[-1]
        candidates = _test_name_candidates(stem)

        matches = sorted(
            m for m in all_modules
            if m != module and m.rsplit(".", 1)[-1] in candidates
        )

        recommendations.append(TestRecommendation(
            affected_module=module,
            test_modules=matches,
            has_coverage=bool(matches),
        ))

    return recommendations
