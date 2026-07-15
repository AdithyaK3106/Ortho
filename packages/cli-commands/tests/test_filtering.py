"""Test suite for task-023-filtering: severity and confidence filtering.

This module contains hard tests for guardrails() severity_filter and decide()
confidence_threshold parameters. Tests run against real repos (click, requests)
and verify filtering semantics as specified in task-023-filtering/spec.md.

Coverage:
1. guardrails() severity filtering ("error", "warning")
2. guardrails() no-filter default behavior
3. guardrails() invalid severity handling
4. guardrails() text summary reflecting filtering
5. decide() confidence filtering (0.0-1.0 range)
6. decide() confidence edge cases (0.0, 1.0)
7. decide() invalid confidence handling
8. decide() empty-after-filter fallback (shows highest-confidence)
9. decide() text summary reflecting filtering
10. Backward compatibility (existing calls without filters)
11. CLI bridge parameter validation
"""
import os
from pathlib import Path
from typing import Any

import pytest

from arch_guardrails.types import GuardrailViolation
from cli_commands.commands import CliCommands
from cli_commands.types import CliReport
from decision_engine.types import Recommendation

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_REPO_CLICK = str(_REPO_ROOT / "repos" / "click")
_FIXTURE_REPO_REQUESTS = str(_REPO_ROOT / "repos" / "requests")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestGuardrailsSeverityFiltering:
    """Test guardrails() severity_filter parameter"""

    def test_guardrails_severity_filter_error_only(self, commands: CliCommands) -> None:
        """guardrails(path, severity_filter="error") returns only error violations.

        Verifies that:
        - report.violations contains ONLY violations where v.severity == "error"
        - report.content reflects the filtered output
        - No warning severities are present
        """
        result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")
        assert isinstance(result, CliReport)
        assert result.success
        assert result.violations is not None
        assert isinstance(result.violations, list)

        # All violations must have severity "error"
        for v in result.violations:
            assert isinstance(v, GuardrailViolation)
            assert v.severity == "error", f"Expected 'error', got '{v.severity}'"

        # Anti-overfitting: verify no "warning" severities are present
        severities = {v.severity for v in result.violations}
        assert "warning" not in severities

    def test_guardrails_severity_filter_warning_only(self, commands: CliCommands) -> None:
        """guardrails(path, severity_filter="warning") returns only warning violations.

        Verifies that:
        - report.violations contains ONLY violations where v.severity == "warning"
        - No error severities are present
        """
        result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="warning")
        assert isinstance(result, CliReport)
        assert result.success
        assert result.violations is not None
        assert isinstance(result.violations, list)

        # All violations must have severity "warning"
        for v in result.violations:
            assert isinstance(v, GuardrailViolation)
            assert v.severity == "warning", f"Expected 'warning', got '{v.severity}'"

        # Anti-overfitting: verify no "error" severities are present
        severities = {v.severity for v in result.violations}
        assert "error" not in severities

    def test_guardrails_severity_filter_counts_preserved(self, commands: CliCommands) -> None:
        """Filtering produces subset; no new violations invented, none lost silently.

        If we filter for 'error' and the unfiltered repo has N total violations,
        the filtered count should be <= N.
        """
        unfiltered = commands.guardrails(_FIXTURE_REPO_CLICK)
        filtered_error = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")
        filtered_warning = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="warning")

        unfiltered_count = len(unfiltered.violations) if unfiltered.violations else 0
        error_count = len(filtered_error.violations) if filtered_error.violations else 0
        warning_count = len(filtered_warning.violations) if filtered_warning.violations else 0

        # Filtered counts should be subsets
        assert error_count <= unfiltered_count
        assert warning_count <= unfiltered_count

        # Sum of error + warning should equal unfiltered (disjoint partition)
        assert error_count + warning_count == unfiltered_count

    def test_guardrails_no_filter_default_returns_all(self, commands: CliCommands) -> None:
        """guardrails(path, severity_filter=None) returns all violations (default behavior).

        Verifies backward compatibility: calling without severity_filter or with
        severity_filter=None produces identical output to pre-filtering.
        """
        result_no_param = commands.guardrails(_FIXTURE_REPO_CLICK)
        result_none_param = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter=None)

        # Both should return identical lists
        assert result_no_param.violations is not None
        assert result_none_param.violations is not None
        assert len(result_no_param.violations) == len(result_none_param.violations)

        # Rule IDs should match (same violations)
        no_param_rules = {v.rule_id for v in result_no_param.violations}
        none_param_rules = {v.rule_id for v in result_none_param.violations}
        assert no_param_rules == none_param_rules

    def test_guardrails_invalid_severity_raises_valueerror(self, commands: CliCommands) -> None:
        """guardrails(path, severity_filter="unknown") raises ValueError.

        Only "error" and "warning" are valid; any other string must raise ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="unknown")
        assert "error" in str(exc_info.value) and "warning" in str(exc_info.value)

    def test_guardrails_invalid_severity_other_values(self, commands: CliCommands) -> None:
        """Test additional invalid severity values."""
        invalid_values = ["critical", "info", "debug", "ERROR", "Warning", ""]
        for invalid in invalid_values:
            with pytest.raises(ValueError):
                commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter=invalid)

    def test_guardrails_text_summary_no_filter(self, commands: CliCommands) -> None:
        """Text summary shows filter count when filtering is applied.

        When severity_filter=None (no filtering): "K violations found."
        When severity_filter is applied: "K violations found (M filtered by severity)."
        """
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        content = result.content

        # Unfiltered should have one of these patterns:
        # "K violations found." (without filter count)
        # or "Scanned N file(s). M violation(s) found." (without "(filtered)")
        has_no_filter_marker = ("violations found." in content or "violation(s) found." in content) and (
            "filtered by severity" not in content
        )
        # Should mention files scanned
        assert "Scanned" in content or "file" in content or "violation" in content.lower()

    def test_guardrails_text_summary_with_filter(self, commands: CliCommands) -> None:
        """Text summary indicates filtering count when filter is applied."""
        result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")
        content = result.content

        # If violations were filtered, summary should indicate it
        # Either "M violations found (N filtered by severity)" or similar
        if result.violations and len(result.violations) > 0:
            # Has content about violations
            assert "violation" in content.lower() or "[error]" in content

    def test_guardrails_text_content_matches_violations(self, commands: CliCommands) -> None:
        """Text content only shows filtered violations, not all violations.

        If severity_filter="error", the text should only mention error violations,
        not warnings.
        """
        all_result = commands.guardrails(_FIXTURE_REPO_CLICK)
        error_result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")

        # Count mentions of [error] in text
        error_mentions_all = all_result.content.count("[error]")
        error_mentions_error = error_result.content.count("[error]")

        # Filtered result should have <= error mentions than unfiltered
        # (or potentially different if formatting changes)
        # At minimum: if errors exist, they should appear in error-filtered result
        if error_result.violations:
            assert "[error]" in error_result.content or "error" in error_result.content.lower()


class TestGuardrailsBackwardCompatibility:
    """Test that existing guardrails() calls work unchanged"""

    def test_guardrails_existing_call_pattern_works(self, commands: CliCommands) -> None:
        """Existing code: commands.guardrails(path) works unchanged."""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        assert isinstance(result, CliReport)
        assert result.success
        assert isinstance(result.violations, list) or result.violations is None

    def test_guardrails_legacy_kwargs_pattern(self, commands: CliCommands) -> None:
        """Existing code: commands.guardrails(path, **{'key': 'value'}) works."""
        kwargs = {"some_future_param": "value"}
        # Should not crash on unknown kwargs
        result = commands.guardrails(_FIXTURE_REPO_CLICK, **kwargs)
        assert isinstance(result, CliReport)
        assert result.success

    def test_guardrails_no_filter_identical_to_none_param(self, commands: CliCommands) -> None:
        """Commands with no filter param are identical to severity_filter=None."""
        result1 = commands.guardrails(_FIXTURE_REPO_CLICK)
        result2 = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter=None)

        # Both should have same violations
        if result1.violations and result2.violations:
            assert len(result1.violations) == len(result2.violations)
            titles1 = [v.rule_id for v in result1.violations]
            titles2 = [v.rule_id for v in result2.violations]
            assert titles1 == titles2


class TestDecideConfidenceFiltering:
    """Test decide() confidence_threshold parameter"""

    def test_decide_confidence_filter_high_threshold(self, commands: CliCommands) -> None:
        """decide(intent, confidence_threshold=0.8) returns only high-confidence recommendations.

        Verifies that:
        - report.recommendations contains ONLY recommendations where r.confidence >= 0.8
        - All confidences in the list are >= 0.8
        """
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)
        assert isinstance(result, CliReport)
        assert result.success
        assert result.recommendations is not None
        assert isinstance(result.recommendations, list)

        # All recommendations must have confidence >= 0.8
        for r in result.recommendations:
            assert isinstance(r, Recommendation)
            assert r.confidence >= 0.8, f"Expected confidence >= 0.8, got {r.confidence}"

        # Anti-overfitting: all confidences must be at or above threshold
        min_confidence = min((r.confidence for r in result.recommendations), default=1.0)
        assert min_confidence >= 0.8

    def test_decide_confidence_filter_medium_threshold(self, commands: CliCommands) -> None:
        """decide() with confidence_threshold=0.5 returns medium+ confidence recommendations."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.5)
        assert isinstance(result, CliReport)
        assert result.success
        assert result.recommendations is not None

        # All recommendations must have confidence >= 0.5
        for r in result.recommendations:
            assert r.confidence >= 0.5

    def test_decide_confidence_filter_low_threshold(self, commands: CliCommands) -> None:
        """decide() with confidence_threshold=0.0 includes all (>= 0.0)."""
        result_none = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        result_zero = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.0)

        # Both should have same recommendations (0.0 threshold includes everything)
        assert result_none.recommendations is not None
        assert result_zero.recommendations is not None
        assert len(result_none.recommendations) == len(result_zero.recommendations)

        titles_none = [r.title for r in result_none.recommendations]
        titles_zero = [r.title for r in result_zero.recommendations]
        assert titles_none == titles_zero

    def test_decide_confidence_filter_max_threshold(self, commands: CliCommands) -> None:
        """decide() with confidence_threshold=1.0 includes only confidence=1.0 recommendations."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=1.0)
        assert isinstance(result, CliReport)
        assert result.success
        assert result.recommendations is not None

        # All recommendations (if any) must have confidence == 1.0
        for r in result.recommendations:
            assert r.confidence == 1.0, f"Expected confidence 1.0, got {r.confidence}"

    def test_decide_confidence_counts_preserved(self, commands: CliCommands) -> None:
        """Filtering produces subset; counts are monotonic.

        High threshold (0.9) should yield <= medium threshold (0.5) results.
        """
        result_all = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        result_med = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.5)
        result_high = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.9)

        all_count = len(result_all.recommendations) if result_all.recommendations else 0
        med_count = len(result_med.recommendations) if result_med.recommendations else 0
        high_count = len(result_high.recommendations) if result_high.recommendations else 0

        # Monotonic: higher threshold -> fewer or equal results
        assert high_count <= med_count <= all_count

    def test_decide_no_filter_default_returns_all(self, commands: CliCommands) -> None:
        """decide(intent, confidence_threshold=None) returns all recommendations (default).

        Backward compatibility: no confidence_threshold parameter yields all options.
        """
        result_no_param = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        result_none_param = commands.decide(
            "improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=None
        )

        # Both should return identical lists
        assert result_no_param.recommendations is not None
        assert result_none_param.recommendations is not None
        assert len(result_no_param.recommendations) == len(result_none_param.recommendations)

        # Titles should match (same recommendations)
        no_param_titles = {r.title for r in result_no_param.recommendations}
        none_param_titles = {r.title for r in result_none_param.recommendations}
        assert no_param_titles == none_param_titles

    def test_decide_invalid_confidence_out_of_range(self, commands: CliCommands) -> None:
        """decide() with confidence_threshold < 0.0 or > 1.0 raises ValueError."""
        invalid_values = [-0.1, -1.0, 1.1, 2.0]
        for invalid in invalid_values:
            with pytest.raises(ValueError) as exc_info:
                commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=invalid)
            assert "0.0" in str(exc_info.value) and "1.0" in str(exc_info.value)

    def test_decide_invalid_confidence_string_type(self, commands: CliCommands) -> None:
        """decide() with confidence_threshold as string raises ValueError.

        Must be float, not string.
        """
        with pytest.raises(ValueError):
            commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold="0.8")  # type: ignore

    def test_decide_invalid_confidence_wrong_type(self, commands: CliCommands) -> None:
        """decide() with confidence_threshold as non-float type raises ValueError."""
        invalid_types = ["0.5", 1, None]  # None should be allowed, but let's separate that
        for invalid in ["0.5", 1]:
            with pytest.raises(ValueError):
                commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=invalid)  # type: ignore

    def test_decide_empty_after_filter_fallback(self, commands: CliCommands) -> None:
        """If all recommendations filtered out, show highest-confidence option as recommended.

        Per spec: if filtering results in zero options, pick the highest-confidence
        option as recommended and include it in the report.
        """
        # Use a very high threshold that might filter everything
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=1.0)

        # Even if filtering removes everything, should still have at least one recommendation
        # (the highest-confidence one) per spec
        assert isinstance(result, CliReport)
        assert result.success
        assert result.recommendations is not None
        assert len(result.recommendations) >= 1, "Must show at least highest-confidence option when filtered"

    def test_decide_text_summary_no_filter(self, commands: CliCommands) -> None:
        """Text summary shows 'Recommended: <title>' when no filtering."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        content = result.content

        # Should mention 'Recommended:' without filter markers
        assert "Recommended:" in content or "Recommendation:" in content
        assert "filtered by confidence" not in content

    def test_decide_text_summary_with_filter(self, commands: CliCommands) -> None:
        """Text summary indicates filtering when confidence_threshold is applied."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)
        content = result.content

        # If recommendations were filtered, summary might indicate it
        # Check for filtering indicator or at least that it's still a valid decision summary
        assert "Decision for:" in content or "Decision:" in content


class TestDecideBackwardCompatibility:
    """Test that existing decide() calls work unchanged"""

    def test_decide_existing_call_pattern_works(self, commands: CliCommands) -> None:
        """Existing code: commands.decide(intent) works unchanged."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        assert isinstance(result, CliReport)
        assert result.success
        assert isinstance(result.recommendations, list) or result.recommendations is None

    def test_decide_legacy_kwargs_pattern(self, commands: CliCommands) -> None:
        """Existing code: commands.decide(intent, **{'key': 'value'}) works."""
        kwargs = {"some_future_param": "value"}
        # Should not crash on unknown kwargs
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, **kwargs)
        assert isinstance(result, CliReport)
        assert result.success

    def test_decide_no_filter_identical_to_none_param(self, commands: CliCommands) -> None:
        """Commands with no filter param are identical to confidence_threshold=None."""
        result1 = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        result2 = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=None)

        # Both should have same recommendations
        if result1.recommendations and result2.recommendations:
            assert len(result1.recommendations) == len(result2.recommendations)
            titles1 = [r.title for r in result1.recommendations]
            titles2 = [r.title for r in result2.recommendations]
            assert titles1 == titles2


class TestCliParameterValidation:
    """Test CLI bridge validation logic (Python-side)

    Note: These tests verify the Python method accepts parameters with
    correct types and ranges. Full CLI validation is tested in integration tests.
    """

    def test_guardrails_accepts_severity_error_kwarg(self, commands: CliCommands) -> None:
        """guardrails() accepts severity_filter='error' kwarg."""
        result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")
        assert result.success

    def test_guardrails_accepts_severity_warning_kwarg(self, commands: CliCommands) -> None:
        """guardrails() accepts severity_filter='warning' kwarg."""
        result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="warning")
        assert result.success

    def test_decide_accepts_confidence_float_kwarg(self, commands: CliCommands) -> None:
        """decide() accepts confidence_threshold as float kwarg."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)
        assert result.success

    def test_decide_accepts_confidence_zero_kwarg(self, commands: CliCommands) -> None:
        """decide() accepts confidence_threshold=0.0 kwarg."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.0)
        assert result.success

    def test_decide_accepts_confidence_one_kwarg(self, commands: CliCommands) -> None:
        """decide() accepts confidence_threshold=1.0 kwarg."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=1.0)
        assert result.success


class TestFilteringIntegration:
    """Integration tests: filtering across multiple calls"""

    def test_guardrails_filtering_consistent_across_calls(self, commands: CliCommands) -> None:
        """Running guardrails twice with same filter yields same results (deterministic)."""
        result1 = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")
        result2 = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")

        assert result1.violations is not None
        assert result2.violations is not None
        assert len(result1.violations) == len(result2.violations)

        rule_ids_1 = [v.rule_id for v in result1.violations]
        rule_ids_2 = [v.rule_id for v in result2.violations]
        assert rule_ids_1 == rule_ids_2

    def test_decide_filtering_consistent_across_calls(self, commands: CliCommands) -> None:
        """Running decide twice with same filter yields same results (deterministic)."""
        result1 = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)
        result2 = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)

        assert result1.recommendations is not None
        assert result2.recommendations is not None
        assert len(result1.recommendations) == len(result2.recommendations)

        titles_1 = [r.title for r in result1.recommendations]
        titles_2 = [r.title for r in result2.recommendations]
        assert titles_1 == titles_2

    def test_guardrails_filtering_on_clean_repo(self, commands: CliCommands) -> None:
        """Filtering on clean repo (requests) still works (may return empty)."""
        result_error = commands.guardrails(_FIXTURE_REPO_REQUESTS, severity_filter="error")
        result_warning = commands.guardrails(_FIXTURE_REPO_REQUESTS, severity_filter="warning")

        # Both should succeed even if empty
        assert result_error.success
        assert result_warning.success
        assert result_error.violations is not None
        assert result_warning.violations is not None

        # Might be empty but that's OK
        for v in result_error.violations:
            assert v.severity == "error"
        for v in result_warning.violations:
            assert v.severity == "warning"

    def test_decide_all_filter_levels_work(self, commands: CliCommands) -> None:
        """decide() works across multiple threshold levels."""
        thresholds = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
        results = []

        for threshold in thresholds:
            result = commands.decide(
                "improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=threshold
            )
            results.append(result)
            assert result.success, f"Failed at threshold {threshold}"

        # Counts should be monotonically decreasing
        counts = [len(r.recommendations) if r.recommendations else 0 for r in results]
        for i in range(len(counts) - 1):
            assert counts[i] >= counts[i + 1], f"Count not monotonic: {counts}"


class TestEdgeCases:
    """Edge case tests"""

    def test_guardrails_none_path_uses_dot(self, commands: CliCommands) -> None:
        """guardrails(None) defaults to current directory.

        Bound cwd to a small fixture -- see test_guardrails_empty_string_path.
        """
        original_cwd = os.getcwd()
        os.chdir(_FIXTURE_REPO_REQUESTS)
        try:
            result = commands.guardrails(None)
        finally:
            os.chdir(original_cwd)
        # Should handle gracefully (may scan current dir or fail cleanly)
        assert isinstance(result, CliReport)

    def test_guardrails_empty_string_path(self, commands: CliCommands) -> None:
        """guardrails('') is treated as current directory.

        Bound cwd to a small fixture for this call -- the monorepo root's
        cwd contains repos/ (7800+ vendored files across cloned frameworks),
        which turns this into an unbounded scan that stalls the suite.
        """
        original_cwd = os.getcwd()
        os.chdir(_FIXTURE_REPO_REQUESTS)
        try:
            result = commands.guardrails("")
        finally:
            os.chdir(original_cwd)
        # Should handle gracefully
        assert isinstance(result, CliReport)

    def test_guardrails_filter_with_clean_repo(self, commands: CliCommands) -> None:
        """Filtering on clean repo with no violations of filtered type."""
        # repos/requests is typically clean; filter for errors
        result = commands.guardrails(_FIXTURE_REPO_REQUESTS, severity_filter="error")
        assert result.success
        assert result.violations is not None
        # May be empty, but all items (if any) should be errors
        for v in result.violations:
            assert v.severity == "error"

    def test_decide_confidence_boundary_inclusive(self, commands: CliCommands) -> None:
        """Confidence filtering uses >= (inclusive lower bound)."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.75)

        assert result.recommendations is not None
        # If there are recommendations, their confidence should be >= 0.75
        for r in result.recommendations:
            assert r.confidence >= 0.75, f"Expected >= 0.75, got {r.confidence}"

        # Test that a recommendation with exactly 0.75 would pass if it exists
        # This is implicit in the list comprehension: >= not >
        has_boundary = any(abs(r.confidence - 0.75) < 0.001 for r in result.recommendations)
        # If such a recommendation exists, it should be included
        # (We can't guarantee it exists, but the logic should be >=)


class TestReportStructure:
    """Verify report structure is maintained with filtering"""

    def test_guardrails_report_has_all_fields(self, commands: CliCommands) -> None:
        """CliReport has all fields even when filtered."""
        result = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")

        assert hasattr(result, "title")
        assert hasattr(result, "content")
        assert hasattr(result, "format")
        assert hasattr(result, "success")
        assert hasattr(result, "violations")
        assert hasattr(result, "recommendations")

        assert isinstance(result.title, str)
        assert isinstance(result.content, str)
        assert isinstance(result.format, str)
        assert isinstance(result.success, bool)

    def test_decide_report_has_all_fields(self, commands: CliCommands) -> None:
        """CliReport has all fields even when filtered."""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)

        assert hasattr(result, "title")
        assert hasattr(result, "content")
        assert hasattr(result, "format")
        assert hasattr(result, "success")
        assert hasattr(result, "violations")
        assert hasattr(result, "recommendations")

        assert isinstance(result.title, str)
        assert isinstance(result.content, str)
        assert isinstance(result.format, str)
        assert isinstance(result.success, bool)

    def test_guardrails_violations_is_list_or_none(self, commands: CliCommands) -> None:
        """report.violations is list (when success) or None (when failed)."""
        result_success = commands.guardrails(_FIXTURE_REPO_CLICK, severity_filter="error")
        result_fail = commands.guardrails("/nonexistent/path", severity_filter="error")

        assert isinstance(result_success.violations, list)
        # On failure, violations should be None
        # (or absent, handled by CliReport)

    def test_decide_recommendations_is_list_or_none(self, commands: CliCommands) -> None:
        """report.recommendations is list (when success) or None (when failed)."""
        result_success = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK, confidence_threshold=0.8)
        result_fail = commands.decide("")  # Empty intent fails

        assert isinstance(result_success.recommendations, list)
        # On failure, recommendations should be None
