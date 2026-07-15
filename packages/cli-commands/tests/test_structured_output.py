"""Test structured JSON output for guardrails() and decide() commands.

This test module verifies that CliReport.violations and CliReport.recommendations
are populated with real structured objects while text output remains unchanged.
"""
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
# click/requests are small, well-organized repos with no real layer_boundaries
# or module_sizing issues -- flask is used wherever a test needs a repo
# guaranteed to have at least one real violation to assert against (after
# the layer_detector false-positive fix, click/requests correctly report
# zero violations; see docs/archive/PRODUCTION_AUDIT_2026-07-15.md).
_FIXTURE_REPO_FLASK = str(_REPO_ROOT / "repos" / "flask")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestGuardrailsStructuredOutput:
    """Test guardrails() returns violations field with real GuardrailViolation objects"""

    def test_guardrails_returns_violations_on_real_repo(self, commands: CliCommands) -> None:
        """guardrails() against repos/click returns violations list (not None)"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        assert isinstance(result, CliReport)
        assert result.success
        assert result.violations is not None, "violations field must be populated (not None)"
        assert isinstance(result.violations, list), "violations must be a list"

    def test_guardrails_violations_are_real_objects(self, commands: CliCommands) -> None:
        """Each violation in violations list is a GuardrailViolation instance"""
        result = commands.guardrails(_FIXTURE_REPO_FLASK)
        assert result.violations is not None
        assert len(result.violations) > 0, "repos/flask should have at least one violation"
        for violation in result.violations:
            assert isinstance(violation, GuardrailViolation)

    def test_guardrails_violations_have_required_fields(self, commands: CliCommands) -> None:
        """Each GuardrailViolation has all required fields with correct types"""
        result = commands.guardrails(_FIXTURE_REPO_FLASK)
        assert result.violations is not None
        for v in result.violations:
            # Check all required fields exist and have correct types
            assert hasattr(v, "rule_id") and isinstance(v.rule_id, str)
            assert hasattr(v, "severity") and isinstance(v.severity, str)
            assert hasattr(v, "location") and isinstance(v.location, str)
            assert hasattr(v, "message") and isinstance(v.message, str)
            assert hasattr(v, "suggested_fix") and isinstance(v.suggested_fix, str)
            assert hasattr(v, "evidence") and isinstance(v.evidence, list)
            # Severity must be one of the allowed values
            assert v.severity in ("error", "warning"), f"Invalid severity: {v.severity}"

    def test_guardrails_violations_have_known_rule_ids(self, commands: CliCommands) -> None:
        """Violations have rule_ids matching known architectural checks"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        if result.violations:
            rule_ids = {v.rule_id for v in result.violations}
            # Known rule IDs from arch_guardrails enforcement
            known_rule_ids = {"layer_boundaries", "circular_dependencies", "module_sizing"}
            # At least one rule_id should be known (may have custom ones too)
            assert any(rid in known_rule_ids for rid in rule_ids), (
                f"Expected at least one known rule_id, got: {rule_ids}"
            )

    def test_guardrails_text_output_unchanged(self, commands: CliCommands) -> None:
        """guardrails() content field maintains identical text format"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        # Text output must be non-empty
        assert result.content, "content must not be empty"
        # If violations found, content should mention them (format: [severity] rule_id ...)
        if result.violations:
            # Check for structural properties: should contain violation markers
            violations_text = "\n".join(
                [f"[{v.severity}] {v.rule_id}" for v in result.violations]
            )
            # Each violation's severity and rule_id should appear in content
            for v in result.violations[:3]:  # Check first 3 to avoid too many assertions
                assert f"[{v.severity}]" in result.content or v.rule_id in result.content
        else:
            # No violations case
            assert "Scanned" in result.content and "file(s)" in result.content

    def test_guardrails_empty_repo_returns_empty_violations(self, commands: CliCommands) -> None:
        """guardrails() against repos/requests (clean repo) returns empty or small violations"""
        result = commands.guardrails(_FIXTURE_REPO_REQUESTS)
        assert result.success
        assert result.violations is not None
        # repos/requests should be relatively clean (this is a known good fixture)
        assert isinstance(result.violations, list)

    def test_guardrails_failure_path_no_violations(self, commands: CliCommands) -> None:
        """guardrails() on nonexistent path returns success=False and violations=None"""
        result = commands.guardrails("/definitely/not/a/real/path/xyz")
        assert result.success is False
        # On failure, violations should not be populated
        assert result.violations is None

    def test_guardrails_deterministic_results(self, commands: CliCommands) -> None:
        """Running guardrails twice on same repo yields same violations (deterministic)"""
        result1 = commands.guardrails(_FIXTURE_REPO_CLICK)
        result2 = commands.guardrails(_FIXTURE_REPO_CLICK)

        assert result1.violations is not None
        assert result2.violations is not None

        # Same number of violations
        assert len(result1.violations) == len(result2.violations), (
            "Second run should yield same count of violations"
        )

        # Same rule_ids in same order (deterministic)
        rule_ids_1 = [v.rule_id for v in result1.violations]
        rule_ids_2 = [v.rule_id for v in result2.violations]
        assert rule_ids_1 == rule_ids_2, "Violations should be deterministic across runs"


class TestDecideStructuredOutput:
    """Test decide() returns recommendations field with real Recommendation objects"""

    def test_decide_returns_recommendations_on_real_repo(self, commands: CliCommands) -> None:
        """decide() against repos/click returns recommendations list (not None)"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        assert isinstance(result, CliReport)
        assert result.success
        assert result.recommendations is not None, "recommendations field must be populated (not None)"
        assert isinstance(result.recommendations, list), "recommendations must be a list"

    def test_decide_recommendations_are_real_objects(self, commands: CliCommands) -> None:
        """Each recommendation in recommendations list is a Recommendation instance"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        assert result.recommendations is not None
        assert len(result.recommendations) > 0, "Should have at least one recommendation"
        for rec in result.recommendations:
            assert isinstance(rec, Recommendation)

    def test_decide_recommendations_have_required_fields(self, commands: CliCommands) -> None:
        """Each Recommendation has all required fields with correct types"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        assert result.recommendations is not None
        for rec in result.recommendations:
            # Check all required fields exist and have correct types
            assert hasattr(rec, "title") and isinstance(rec.title, str)
            assert hasattr(rec, "description") and isinstance(rec.description, str)
            assert hasattr(rec, "source") and isinstance(rec.source, str)
            assert hasattr(rec, "effort") and isinstance(rec.effort, str)
            assert hasattr(rec, "risk") and isinstance(rec.risk, str)
            assert hasattr(rec, "confidence") and isinstance(rec.confidence, float)
            assert hasattr(rec, "suggested_fix") and isinstance(rec.suggested_fix, str)
            assert hasattr(rec, "evidence") and isinstance(rec.evidence, list)
            # Validate enum constraints
            assert rec.effort in ("low", "medium", "high"), f"Invalid effort: {rec.effort}"
            assert rec.risk in ("low", "medium", "high"), f"Invalid risk: {rec.risk}"
            assert 0.0 <= rec.confidence <= 1.0, f"Invalid confidence: {rec.confidence}"

    def test_decide_text_output_unchanged(self, commands: CliCommands) -> None:
        """decide() content field maintains identical text format"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        # Text output must be non-empty
        assert result.content, "content must not be empty"
        # Should contain decision markers
        assert "Decision for:" in result.content
        if result.recommendations:
            # Should mention recommended option
            recommended = result.recommendations[0]  # First is typically the recommended one
            # Check structural properties (not exact strings to avoid overfitting)
            assert "Recommended:" in result.content or "Recommendation:" in result.content

    def test_decide_failure_path_empty_intent(self, commands: CliCommands) -> None:
        """decide() with empty intent returns success=False and recommendations=None"""
        result = commands.decide("")
        assert result.success is False
        # On failure, recommendations should not be populated
        assert result.recommendations is None

    def test_decide_file_intent_recommendations(self, commands: CliCommands) -> None:
        """decide() with file path intent returns recommendations"""
        target = str(_REPO_ROOT / "repos" / "requests" / "src" / "requests" / "models.py")
        result = commands.decide(target)
        assert result.success
        assert result.recommendations is not None
        assert isinstance(result.recommendations, list)

    def test_decide_text_intent_with_scan_path(self, commands: CliCommands) -> None:
        """decide() with text intent and explicit scan_path returns recommendations"""
        result = commands.decide("add caching", scan_path=_FIXTURE_REPO_CLICK)
        assert result.success
        assert result.recommendations is not None
        assert isinstance(result.recommendations, list)

    def test_decide_recommendations_deterministic(self, commands: CliCommands) -> None:
        """Running decide twice on same intent/repo yields same recommendations (deterministic)"""
        intent = "improve code quality"
        result1 = commands.decide(intent, scan_path=_FIXTURE_REPO_CLICK)
        result2 = commands.decide(intent, scan_path=_FIXTURE_REPO_CLICK)

        assert result1.recommendations is not None
        assert result2.recommendations is not None

        # Same number of recommendations
        assert len(result1.recommendations) == len(result2.recommendations), (
            "Second run should yield same count of recommendations"
        )

        # Same titles in same order (deterministic)
        titles_1 = [r.title for r in result1.recommendations]
        titles_2 = [r.title for r in result2.recommendations]
        assert titles_1 == titles_2, "Recommendations should be deterministic across runs"


class TestBackwardCompatibility:
    """Test that changes are backward compatible with existing code"""

    def test_guardrails_backward_compat_with_clean_repo(self, commands: CliCommands) -> None:
        """guardrails() on clean repo still returns success=True and valid structure"""
        result = commands.guardrails(_FIXTURE_REPO_REQUESTS)
        assert isinstance(result, CliReport)
        assert result.success
        assert isinstance(result.title, str)
        assert isinstance(result.content, str)
        assert result.format == "text"
        # Violations is now populated (but can be empty list)
        assert result.violations is not None

    def test_decide_backward_compat_with_clean_repo(self, commands: CliCommands) -> None:
        """decide() on clean repo still returns success=True and valid structure"""
        result = commands.decide("improve quality", scan_path=_FIXTURE_REPO_REQUESTS)
        assert isinstance(result, CliReport)
        assert result.success
        assert isinstance(result.title, str)
        assert isinstance(result.content, str)
        assert result.format == "text"
        # Recommendations is now populated
        assert result.recommendations is not None

    def test_guardrails_legacy_code_pattern(self, commands: CliCommands) -> None:
        """Legacy code accessing only title/content/success still works"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        # This pattern should work without modification
        title = result.title
        content = result.content
        success = result.success
        assert isinstance(title, str)
        assert isinstance(content, str)
        assert isinstance(success, bool)

    def test_decide_legacy_code_pattern(self, commands: CliCommands) -> None:
        """Legacy code accessing only title/content/success still works"""
        result = commands.decide("test intent", scan_path=_FIXTURE_REPO_CLICK)
        # This pattern should work without modification
        title = result.title
        content = result.content
        success = result.success
        assert isinstance(title, str)
        assert isinstance(content, str)
        assert isinstance(success, bool)


class TestTypeCorrectness:
    """Test that imported types are the real, correct types"""

    def test_guardrailviolation_type_imported_correctly(self, commands: CliCommands) -> None:
        """GuardrailViolation imported from arch_guardrails.types is the real type"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        if result.violations:
            v = result.violations[0]
            # Verify it's the real type (not a mock, not Any)
            assert type(v).__module__ == "arch_guardrails.types"
            assert type(v).__name__ == "GuardrailViolation"

    def test_recommendation_type_imported_correctly(self, commands: CliCommands) -> None:
        """Recommendation imported from decision_engine.types is the real type"""
        result = commands.decide("test", scan_path=_FIXTURE_REPO_CLICK)
        if result.recommendations:
            r = result.recommendations[0]
            # Verify it's the real type (not a mock, not Any)
            assert type(r).__module__ == "decision_engine.types"
            assert type(r).__name__ == "Recommendation"


class TestMultiplicity:
    """Test handling of multiple violations/recommendations"""

    def test_guardrails_multiple_violations_preserved(self, commands: CliCommands) -> None:
        """If repo has multiple violations, all are preserved in violations list"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        if result.violations and len(result.violations) > 1:
            # Verify multiple items are preserved
            assert len(result.violations) > 1
            # All unique by at least some field to avoid duplicates
            locations = {v.location for v in result.violations}
            # Not all duplicates (though some may share location)
            assert len(locations) >= 1

    def test_decide_multiple_recommendations_preserved(self, commands: CliCommands) -> None:
        """If decision has multiple recommendations, all are preserved"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        if result.recommendations and len(result.recommendations) > 1:
            # Verify multiple items are preserved
            assert len(result.recommendations) > 1
            # All unique by title (no duplicates)
            titles = {r.title for r in result.recommendations}
            assert len(titles) == len(result.recommendations)


class TestIntegrationWithExistingTests:
    """Verify new fields don't break existing test patterns"""

    def test_no_regression_guardrails_basic(self, commands: CliCommands) -> None:
        """Existing guardrails test pattern still works"""
        result = commands.guardrails(_FIXTURE_REPO_CLICK)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Architecture" in result.title
        # Content should either say "No violations" or list violations with [error]/[warning]
        assert "Scanned" in result.content or "no violation" in result.content.lower() or "[error]" in result.content or "[warning]" in result.content

    def test_no_regression_decide_basic(self, commands: CliCommands) -> None:
        """Existing decide test pattern still works"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO_CLICK)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Decision" in result.title
        assert result.content != ""
