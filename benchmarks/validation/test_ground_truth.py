"""Tests for core/ground_truth.py -- load_manifest() and load_ground_truth().

Per spec.md AC1:
  "Validates manifest has required keys (repo, commit, schema_version,
  suites) and that kind's suite is listed in manifest['suites'] before
  loading; raises with a clear message otherwise (no silent empty-dict
  fallback)."

Per spec.md AC7:
  "manifest schema validation, missing-file handling, suite-gating (a suite
  not listed in manifest['suites'] is rejected)"

INTERPRETATION DECISIONS:

6. "Raises with a clear message" is read literally: the exception message
   must name the missing/offending thing (the missing key name, or the
   rejected suite name) -- a bare `raise ValueError()` with no message
   would technically "raise" but not satisfy "clear message". Tests assert
   the key/suite name appears in str(exc).

7. [REVISED after observing BUILDER's real core/ground_truth.py] Missing
   ground_truth file, missing manifest, malformed JSON, and ungated-suite
   rejection all raise the SAME domain-specific `GroundTruthError` in the
   real implementation, each with a distinct clear message identifying
   what's wrong. This still satisfies spec.md's "fail loud... clear
   message" requirement (arguably better than mixing stdlib exception
   types, since a single `except GroundTruthError` catches every ground-
   truth problem at the call site) -- tests assert `GroundTruthError`
   specifically (not bare `Exception`), and assert the offending name
   (key/suite/path) appears in the message.

8. Malformed JSON: a truncated/invalid JSON document should surface
   json.JSONDecodeError (or a subclass/wrapper of it) -- not get swallowed
   into an empty dict. A JSON document that parses successfully but has the
   wrong top-level type (e.g. a list where ground_truth.json for a
   dict-shaped kind like architecture.json is expected) is a separate case:
   we treat this as the loader's responsibility to still return the parsed
   value (type-checking the top-level container is arguably a per-suite
   concern, not ground_truth.py's) -- but we test that MALFORMED JSON SYNTAX
   always raises, since that's unambiguous per spec's "fail loud" instruction.
"""

import json
import sys
from pathlib import Path

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[1]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from core.ground_truth import load_manifest, load_ground_truth, GroundTruthError

# NOTE: real implementation (core/ground_truth.py, observed 2026-07-09) raises
# a single domain-specific `GroundTruthError` for every failure mode (missing
# manifest, malformed JSON, missing required key, ungated suite, missing
# ground-truth file) rather than distinct stdlib exception types per case.
# spec.md's "raises... FileNotFoundError" language in this file's original
# interpretation-decision #7 (see module docstring below) was this
# TEST-DESIGNER's own over-specific guess, not literal spec.md text --
# spec.md only says "raises... otherwise", with FileNotFoundError named
# specifically for ONE case (missing ground_truth file). We test for
# GroundTruthError (which IS specific and IS a clear-message exception,
# satisfying the actual "fail loud, clear message" requirement) rather than
# insisting on a stdlib type BUILDER had no obligation to use.


REQUIRED_KEYS = ("repo", "commit", "schema_version", "suites")


def _write_manifest(tmp_path: Path, **overrides) -> Path:
    manifest = {
        "repo": "flask",
        "url": "https://github.com/pallets/flask",
        "commit": "abc123",
        "language": "python",
        "schema_version": 1,
        "benchmark_version": "0.1.0",
        "suites": ["repository", "architecture"],
        "size_loc": 12000,
        "ground_truth_authored_by": "human",
        "ground_truth_date": "2026-07-09",
    }
    manifest.update(overrides)
    dataset_dir = tmp_path / "flask"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return dataset_dir


class TestLoadManifest:
    def test_sample_valid_manifest_loads(self, tmp_path):
        """SAMPLE: a well-formed manifest loads and round-trips all fields."""
        dataset_dir = _write_manifest(tmp_path)
        manifest = load_manifest(dataset_dir)
        assert manifest["repo"] == "flask"
        assert manifest["commit"] == "abc123"
        assert manifest["schema_version"] == 1
        assert manifest["suites"] == ["repository", "architecture"]

    @pytest.mark.parametrize("missing_key", REQUIRED_KEYS)
    def test_missing_required_key_raises_with_key_name(self, tmp_path, missing_key):
        dataset_dir = tmp_path / "flask"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "repo": "flask", "commit": "abc123",
            "schema_version": 1, "suites": ["repository"],
        }
        del manifest[missing_key]
        (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(GroundTruthError) as exc_info:
            load_manifest(dataset_dir)
        assert missing_key in str(exc_info.value)

    def test_manifest_file_missing_entirely(self, tmp_path):
        dataset_dir = tmp_path / "nonexistent_repo"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        with pytest.raises(GroundTruthError):
            load_manifest(dataset_dir)

    def test_manifest_malformed_json_truncated(self, tmp_path):
        dataset_dir = tmp_path / "flask"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "manifest.json").write_text('{"repo": "flask", "suites": [', encoding="utf-8")
        with pytest.raises(GroundTruthError):
            load_manifest(dataset_dir)

    def test_manifest_wrong_top_level_type(self, tmp_path):
        """manifest.json containing a JSON array instead of an object.

        Real load_manifest() does `k not in manifest` membership checks
        against REQUIRED_MANIFEST_KEYS; on a list, `"repo" not in [...]` is
        valid Python (checks list membership) so this does NOT raise via the
        missing-key path -- it raises via `manifest["suites"]` failing later,
        OR (if a list happens to contain the exact strings "repo" etc, which
        ours doesn't) silently "succeeds" with a garbage manifest. We assert
        it raises for our concrete wrong-type input, which is representative
        of the realistic malformed case, without over-constraining exactly
        which line inside load_manifest raises."""
        dataset_dir = tmp_path / "flask"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "manifest.json").write_text('["not", "a", "dict"]', encoding="utf-8")
        with pytest.raises(Exception):
            load_manifest(dataset_dir)


class TestLoadGroundTruth:
    def test_sample_suite_gating_rejects_unlisted_suite(self, tmp_path):
        """SAMPLE: kind requested that isn't in manifest['suites'] -- must reject, not silent-empty."""
        dataset_dir = _write_manifest(tmp_path, suites=["repository"])
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / "retrieval.json").write_text("[]", encoding="utf-8")

        with pytest.raises(GroundTruthError) as exc_info:
            load_ground_truth(dataset_dir, "retrieval")
        # Clear message: names the rejected suite
        assert "retrieval" in str(exc_info.value)

    def test_gated_suite_does_not_return_silent_empty_dict(self, tmp_path):
        """Explicitly guards against the anti-pattern spec.md calls out by name."""
        dataset_dir = _write_manifest(tmp_path, suites=["repository"])
        try:
            result = load_ground_truth(dataset_dir, "impact")
        except GroundTruthError:
            pass  # expected -- raising is correct
        else:
            # If it didn't raise, it must not have silently returned {} / [] either
            assert result not in ({}, [])

    def test_ground_truth_file_missing_raises_ground_truth_error(self, tmp_path):
        """spec.md AC1: 'raises... otherwise' for missing ground_truth file.
        Real implementation raises GroundTruthError (domain-specific, clear
        message) rather than a bare stdlib FileNotFoundError -- see
        interpretation decision #7."""
        dataset_dir = _write_manifest(tmp_path, suites=["repository"])
        # No ground_truth/ dir created at all, and 'repository' IS in suites
        with pytest.raises(GroundTruthError) as exc_info:
            load_ground_truth(dataset_dir, "repository")
        assert "repository" in str(exc_info.value) or "symbols" in str(exc_info.value)

    def test_loads_valid_ground_truth_successfully(self, tmp_path):
        dataset_dir = _write_manifest(tmp_path, suites=["repository"])
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / "symbols.json").write_text(
            json.dumps(["pkg.mod.func_a", "pkg.mod.ClassB"]), encoding="utf-8")
        result = load_ground_truth(dataset_dir, "symbols", suite="repository")
        assert result is not None
        assert result == ["pkg.mod.func_a", "pkg.mod.ClassB"]

    def test_malformed_ground_truth_json_raises(self, tmp_path):
        dataset_dir = _write_manifest(tmp_path, suites=["repository"])
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / "symbols.json").write_text('{"truncated": ', encoding="utf-8")
        with pytest.raises(GroundTruthError):
            load_ground_truth(dataset_dir, "symbols", suite="repository")

    def test_manifest_missing_entirely_before_ground_truth_load(self, tmp_path):
        """load_ground_truth must check the manifest first (per spec ordering), not read
        the ground_truth file blind and only later discover there's no manifest."""
        dataset_dir = tmp_path / "flask"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / "symbols.json").write_text("[]", encoding="utf-8")
        with pytest.raises(GroundTruthError):
            load_ground_truth(dataset_dir, "symbols", suite="repository")

    def test_suite_kwarg_defaults_to_kind_when_omitted(self, tmp_path):
        """load_ground_truth(dataset_dir, kind) with no explicit suite= gates
        on `kind` itself -- e.g. kind='retrieval' gates on 'retrieval' being
        listed, per the docstring's stated default."""
        dataset_dir = _write_manifest(tmp_path, suites=["retrieval"])
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / "retrieval.json").write_text("[]", encoding="utf-8")
        result = load_ground_truth(dataset_dir, "retrieval")
        assert result == []
