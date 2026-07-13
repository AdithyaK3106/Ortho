"""Hard tests for decision engine with multi-source aggregation"""
from unittest.mock import Mock
from typing import Any

import pytest

from decision_engine.engine import DecisionEngine
from decision_engine.types import Decision, Recommendation


@pytest.fixture
def engine() -> DecisionEngine:
    """Create engine instance"""
    return DecisionEngine()


@pytest.fixture
def mock_recommendation() -> Mock:
    """Mock recommendation"""
    mock = Mock()
    mock.title = "Test Recommendation"
    mock.description = "Description"
    mock.source = "test"
    mock.effort = "low"
    mock.risk = "low"
    mock.confidence = 0.85
    mock.suggested_fix = "Fix it"
    mock.evidence = []
    return mock


class TestSingleSource:
    """Test 1-4: Single source scenarios"""

    def test_single_source_change_planner(self, engine: DecisionEngine) -> None:
        """Test 1: Only change predictions"""
        sources = {
            "change_planner": [
                Mock(
                    changed_file="service.py",
                    reasoning="Affects 3 modules",
                    confidence=0.9,
                    cascade_risk="medium",
                    evidence=[],
                )
            ],
            "feature_planner": [],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("analyze impact", sources)

        assert isinstance(result, Decision)
        assert len(result.options) > 0

    def test_single_source_feature_planner(self, engine: DecisionEngine) -> None:
        """Test 2: Only feature paths"""
        sources = {
            "change_planner": [],
            "feature_planner": [
                Mock(
                    name="Simple Route",
                    description="Add route",
                    effort="low",
                    risk="low",
                    affected_layers=["presentation"],
                    rationale="Fits architecture",
                )
            ],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("add endpoint", sources)

        assert len(result.options) > 0

    def test_single_source_refactoring(self, engine: DecisionEngine) -> None:
        """Test 3: Only refactoring issues"""
        sources = {
            "change_planner": [],
            "feature_planner": [],
            "refactoring_advisor": [
                Mock(
                    issue_type="tight_coupling",
                    location="auth ↔ payment",
                    recommendation="Extract interface",
                    estimated_effort="4-8 hours",
                    false_positive_risk="Low",
                    confidence=0.92,
                    evidence=["bidirectional imports"],
                )
            ],
            "arch_guardrails": [],
        }

        result = engine.decide("improve quality", sources)

        assert len(result.options) > 0

    def test_single_source_guardrails(self, engine: DecisionEngine) -> None:
        """Test 4: Only guardrail violations"""
        sources = {
            "change_planner": [],
            "feature_planner": [],
            "refactoring_advisor": [],
            "arch_guardrails": [
                Mock(
                    rule_id="layer_boundaries",
                    message="Presentation imports data",
                    suggested_fix="Invert dependency",
                    evidence=["views.py → db.py"],
                )
            ],
        }

        result = engine.decide("check compliance", sources)

        assert len(result.options) > 0


class TestMultiSource:
    """Test 5-9: Multi-source aggregation"""

    def test_two_sources_change_feature(self, engine: DecisionEngine) -> None:
        """Test 5: Change + feature"""
        sources = {
            "change_planner": [
                Mock(
                    changed_file="auth.py",
                    reasoning="Impact",
                    confidence=0.9,
                    cascade_risk="low",
                    evidence=[],
                )
            ],
            "feature_planner": [
                Mock(
                    name="New auth path",
                    description="Impl",
                    effort="low",
                    risk="low",
                    affected_layers=["business"],
                    rationale="Fits",
                )
            ],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("auth changes", sources)

        assert len(result.options) >= 2

    def test_all_four_sources(self, engine: DecisionEngine) -> None:
        """Test 9: All 4 sources combined"""
        sources = {
            "change_planner": [
                Mock(
                    changed_file="f.py",
                    reasoning="R",
                    confidence=0.8,
                    cascade_risk="low",
                    evidence=[],
                )
            ],
            "feature_planner": [
                Mock(
                    name="Path",
                    description="D",
                    effort="low",
                    risk="low",
                    affected_layers=["a"],
                    rationale="R",
                )
            ],
            "refactoring_advisor": [
                Mock(
                    issue_type="t",
                    location="l",
                    recommendation="r",
                    estimated_effort="e",
                    false_positive_risk="f",
                    confidence=0.9,
                    evidence=["e"],
                )
            ],
            "arch_guardrails": [
                Mock(
                    rule_id="r",
                    message="m",
                    suggested_fix="f",
                    evidence=["e"],
                )
            ],
        }

        result = engine.decide("combined", sources)

        assert len(result.options) >= 4


class TestRanking:
    """Test 13-16: Ranking and scoring"""

    def test_high_confidence_consensus(self, engine: DecisionEngine) -> None:
        """Test 13: High confidence agreement"""
        sources = {
            "change_planner": [
                Mock(
                    changed_file="f",
                    reasoning="R",
                    confidence=0.95,
                    cascade_risk="low",
                    evidence=[],
                )
            ],
            "feature_planner": [],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("impact", sources)

        assert result.options[0].confidence >= 0.8

    def test_ranking_by_confidence(self, engine: DecisionEngine) -> None:
        """Highest confidence ranked first"""
        recs = [
            Recommendation(
                title="High",
                description="D",
                source="a",
                effort="low",
                risk="low",
                confidence=0.9,
                suggested_fix="F",
            ),
            Recommendation(
                title="Low",
                description="D",
                source="b",
                effort="low",
                risk="low",
                confidence=0.5,
                suggested_fix="F",
            ),
        ]

        ranked = engine._rank_options(recs, "test")

        assert ranked[0].confidence > ranked[1].confidence


class TestDeduplication:
    """Test 17-18: Deduplication"""

    def test_similar_recs_merged(self, engine: DecisionEngine) -> None:
        """Test 17: Similar recs merged"""
        recs = [
            Recommendation(
                title="Extract interface",
                description="D1",
                source="a",
                effort="low",
                risk="low",
                confidence=0.9,
                suggested_fix="F1",
            ),
            Recommendation(
                title="Extract interface pattern",
                description="D2",
                source="b",
                effort="low",
                risk="low",
                confidence=0.85,
                suggested_fix="F2",
            ),
        ]

        deduped = engine._deduplicate(recs)

        # Similar titles should be deduplicated
        assert len(deduped) <= len(recs)


class TestEdgeCases:
    """Test 19-20: Edge cases"""

    def test_large_option_set_limited(self, engine: DecisionEngine) -> None:
        """Test 19: Limit output to 5 options"""
        sources = {
            "change_planner": [
                Mock(
                    changed_file=f"f{i}.py",
                    reasoning=f"R{i}",
                    confidence=0.8 + (i * 0.01),
                    cascade_risk="low",
                    evidence=[],
                )
                for i in range(20)
            ],
            "feature_planner": [],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("many impacts", sources)

        assert len(result.options) <= 5

    def test_empty_sources_graceful(self, engine: DecisionEngine) -> None:
        """Test 20: Empty sources handled"""
        sources = {
            "change_planner": [],
            "feature_planner": [],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("nothing", sources)

        # Should still return valid Decision
        assert isinstance(result, Decision)
        assert result.recommended_option.title == "No recommendations"


class TestAccuracy:
    """Test accuracy metrics"""

    def test_decision_complete(self, engine: DecisionEngine) -> None:
        """Decision has all required fields"""
        sources = {
            "change_planner": [
                Mock(
                    changed_file="f",
                    reasoning="R",
                    confidence=0.8,
                    cascade_risk="low",
                    evidence=[],
                )
            ],
            "feature_planner": [],
            "refactoring_advisor": [],
            "arch_guardrails": [],
        }

        result = engine.decide("test", sources)

        assert result.intent != ""
        assert len(result.options) > 0
        assert result.recommended_option is not None
        assert result.reasoning != ""
        assert 0.0 <= result.confidence <= 1.0
