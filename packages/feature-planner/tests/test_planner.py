"""Hard test cases for feature planning with 3+ distinct paths per feature"""
from typing import Any

import pytest

from feature_planner.planner import FeaturePlanner
from feature_planner.types import FeaturePlan


@pytest.fixture
def planner(mock_arch_model: Any) -> FeaturePlanner:
    """Create planner with mock"""
    return FeaturePlanner(arch_model=mock_arch_model)


class TestEndpointFeatures:
    """Test 1-4: API endpoint features"""

    def test_simple_rest_endpoint(self, planner: FeaturePlanner) -> None:
        """Test 1: Add user search endpoint"""
        result = planner.plan_feature("add user search endpoint")

        assert isinstance(result, FeaturePlan)
        assert result.feature_type == "endpoint"
        assert len(result.paths) >= 3
        assert all(p.effort in ("low", "medium", "high") for p in result.paths)
        assert all(p.risk in ("low", "medium", "high") for p in result.paths)

    def test_endpoint_with_authentication(self, planner: FeaturePlanner) -> None:
        """Test 2: Add admin endpoint"""
        result = planner.plan_feature("add admin endpoint for users")

        assert result.feature_type == "endpoint"
        assert len(result.paths) >= 3

    def test_endpoint_microservices_style(self, planner: FeaturePlanner) -> None:
        """Test 3: Endpoint planning considers architecture"""
        result = planner.plan_feature("add search endpoint")

        assert result.feature_type == "endpoint"
        assert len(result.paths) >= 3

    def test_variety_endpoint_paths(self, planner: FeaturePlanner) -> None:
        """Test 4: Verify paths differ materially (not just reordered)"""
        result = planner.plan_feature("add new endpoint")

        efforts = [p.effort for p in result.paths]
        risks = [p.risk for p in result.paths]

        # Paths should differ in effort or risk (not identical)
        assert len(set(efforts)) > 1 or len(set(risks)) > 1


class TestServiceFeatures:
    """Test 5-8: Service layer features"""

    def test_background_job_celery(self, planner: FeaturePlanner) -> None:
        """Test 5: Add notification background job"""
        result = planner.plan_feature("add notification background job")

        assert result.feature_type == "service"
        assert len(result.paths) >= 3
        assert result.paths[0].effort in ("low", "medium", "high")

    def test_async_service(self, planner: FeaturePlanner) -> None:
        """Test 6: Add async worker task"""
        result = planner.plan_feature("add async worker task for processing")

        assert result.feature_type == "service"
        assert len(result.paths) >= 3

    def test_caching_layer(self, planner: FeaturePlanner) -> None:
        """Test 7: Add caching for expensive queries"""
        result = planner.plan_feature("add caching for expensive queries")

        assert result.feature_type == "cross_cutting"  # Caching is cross-cutting
        assert len(result.paths) >= 3

    def test_rate_limiting(self, planner: FeaturePlanner) -> None:
        """Test 8: Add rate limiting to API"""
        result = planner.plan_feature("add rate limiting to API")

        assert result.feature_type == "cross_cutting"
        assert len(result.paths) >= 3


class TestDataLayerFeatures:
    """Test 9-11: Data layer features"""

    def test_database_migration(self, planner: FeaturePlanner) -> None:
        """Test 9: Add database migration"""
        result = planner.plan_feature("add users.role column to database")

        assert result.feature_type == "data_layer"
        assert len(result.paths) >= 3

    def test_data_validation(self, planner: FeaturePlanner) -> None:
        """Test 10: Add database schema"""
        result = planner.plan_feature("add database schema for users")

        assert result.feature_type == "data_layer"
        assert len(result.paths) >= 3

    def test_repository_pattern(self, planner: FeaturePlanner) -> None:
        """Test 11: Add repository pattern"""
        result = planner.plan_feature("add abstraction layer for data access")

        assert result.feature_type == "data_layer"
        assert len(result.paths) >= 3


class TestCrossCuttingFeatures:
    """Test 12-13: Cross-cutting concerns"""

    def test_observability_logging(self, planner: FeaturePlanner) -> None:
        """Test 12: Add structured logging"""
        result = planner.plan_feature("add structured logging")

        assert result.feature_type == "cross_cutting"
        assert len(result.paths) >= 3

    def test_feature_flags(self, planner: FeaturePlanner) -> None:
        """Test 13: Add feature flags for A/B testing"""
        result = planner.plan_feature("add feature flags for A/B testing")

        assert result.feature_type == "cross_cutting"
        assert len(result.paths) >= 3


class TestBugfixFeatures:
    """Regression guard for a real bug found live: orchestrate() feeds
    architecture-finding descriptions ("Circular dependency: ... -> Break
    cycle by extracting abstraction") straight into plan_feature() as the
    intent, but none of the original 5 categories are shaped like "fix a
    bug" -- only "add a feature". Every such call silently fell through to
    "infrastructure" and produced nonsense (Terraform/service-registry
    suggestions for a one-file circular-import fix)."""

    def test_break_circular_import(self, planner: FeaturePlanner) -> None:
        """The exact intent string that surfaced the bug."""
        result = planner.plan_feature("break the concurrency circular import")

        assert result.feature_type == "bugfix"
        assert len(result.paths) >= 3

    def test_fix_bug_wording(self, planner: FeaturePlanner) -> None:
        result = planner.plan_feature("fix the login validation bug")

        assert result.feature_type == "bugfix"

    def test_bugfix_wins_over_incidental_keyword_overlap(self, planner: FeaturePlanner) -> None:
        """'fix the login validation bug' also contains 'validation', a
        cross_cutting keyword -- bugfix language must win, since the intent
        is to repair something, not add a new cross-cutting concern."""
        result = planner.plan_feature("fix the login validation bug")

        assert result.feature_type == "bugfix"
        assert result.feature_type != "cross_cutting"

    def test_refactor_wording(self, planner: FeaturePlanner) -> None:
        result = planner.plan_feature("refactor the payment processor")

        assert result.feature_type == "bugfix"

    def test_genuine_feature_requests_unaffected(self, planner: FeaturePlanner) -> None:
        """The new bugfix category must not swallow real feature requests
        that happen to share no bugfix vocabulary."""
        assert planner.plan_feature("add user authentication").feature_type == "cross_cutting"
        assert planner.plan_feature("add a database migration for user roles").feature_type == "data_layer"
        assert planner.plan_feature("add caching to the formatter").feature_type == "cross_cutting"

    def test_bugfix_paths_have_rationale_and_valid_enums(self, planner: FeaturePlanner) -> None:
        result = planner.plan_feature("fix the circular dependency")

        assert len(result.paths) >= 3
        assert all(p.rationale for p in result.paths)
        assert all(p.effort in ("low", "medium", "high") for p in result.paths)
        assert all(p.risk in ("low", "medium", "high") for p in result.paths)


class TestVarietyRequirement:
    """Test 14-15: Verify variety in paths"""

    def test_paths_return_multiple(self, planner: FeaturePlanner) -> None:
        """Test 14: Verify ≥3 distinct paths returned"""
        result = planner.plan_feature("add any feature")

        assert len(result.paths) >= 3
        # All paths should be different (at least names)
        names = [p.name for p in result.paths]
        assert len(set(names)) == len(names)  # All unique

    def test_paths_differ_materially(self, planner: FeaturePlanner) -> None:
        """Test 15: Paths differ in layer, effort, or risk"""
        result = planner.plan_feature("implement a feature")

        # Extract effort/risk profiles
        profiles = [
            (p.effort, p.risk, len(p.affected_layers))
            for p in result.paths
        ]

        # Not all profiles should be identical
        assert len(set(profiles)) > 1 or len(result.paths) > 3


class TestAccuracy:
    """Test accuracy metrics"""

    def test_all_paths_valid(self, planner: FeaturePlanner) -> None:
        """All paths have valid effort/risk"""
        result = planner.plan_feature("add a feature")

        for path in result.paths:
            assert path.effort in ("low", "medium", "high")
            assert path.risk in ("low", "medium", "high")
            assert len(path.affected_layers) > 0
            assert path.name != ""
            assert path.description != ""

    def test_paths_have_rationale(self, planner: FeaturePlanner) -> None:
        """Each path should have rationale"""
        result = planner.plan_feature("add a feature")

        for path in result.paths:
            assert path.rationale != ""
            assert len(path.rationale) > 10

    def test_feature_type_classification(self, planner: FeaturePlanner) -> None:
        """Feature type classification works"""
        tests = [
            ("add endpoint", "endpoint"),
            ("create route", "endpoint"),
            ("add service", "service"),
            ("add worker", "service"),
            ("add database", "data_layer"),
            ("add schema", "data_layer"),
            ("add logging", "cross_cutting"),
            ("add auth", "cross_cutting"),
        ]

        for intent, expected_type in tests:
            result = planner.plan_feature(intent)
            assert result.feature_type == expected_type
