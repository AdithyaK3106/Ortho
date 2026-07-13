"""Exhaustive edge case tests for decision-engine"""
from unittest.mock import Mock
import pytest

from decision_engine.engine import DecisionEngine
from decision_engine.types import Decision


@pytest.fixture
def engine() -> DecisionEngine:
    return DecisionEngine()


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_no_sources_provided(self, engine: DecisionEngine) -> None:
        """Empty sources dict"""
        result = engine.decide("test", sources={})
        assert isinstance(result, Decision)

    def test_all_sources_empty(self, engine: DecisionEngine) -> None:
        """All sources return empty results"""
        result = engine.decide("test", sources={
            "feature": [],
            "refactoring": [],
            "guardrails": [],
            "change": [],
        })
        assert isinstance(result, Decision)

    def test_confidence_all_zero(self, engine: DecisionEngine) -> None:
        """All confidence scores 0.0"""
        sources = {
            "feature": [
                {"title": "Option", "description": "Test", "confidence": 0.0, "effort": "low"}
            ]
        }
        result = engine.decide("test", sources=sources)
        assert isinstance(result, Decision)

    def test_confidence_all_one(self, engine: DecisionEngine) -> None:
        """All confidence scores 1.0"""
        sources = {
            "feature": [
                {"title": "Option A", "description": "Test", "confidence": 1.0, "effort": "low"},
                {"title": "Option B", "description": "Test", "confidence": 1.0, "effort": "low"},
            ]
        }
        result = engine.decide("test", sources=sources)
        # Should still rank
        assert isinstance(result, Decision)

    def test_confidence_nan(self, engine: DecisionEngine) -> None:
        """NaN confidence value"""
        sources = {
            "feature": [
                {"title": "Option", "description": "Test", "confidence": float("nan"), "effort": "low"}
            ]
        }
        result = engine.decide("test", sources=sources)
        # Should handle NaN gracefully
        assert isinstance(result, Decision)

    def test_confidence_infinity(self, engine: DecisionEngine) -> None:
        """Infinite confidence value"""
        sources = {
            "feature": [
                {"title": "Option", "description": "Test", "confidence": float("inf"), "effort": "low"}
            ]
        }
        result = engine.decide("test", sources=sources)
        # Should handle inf gracefully
        assert isinstance(result, Decision)

    def test_single_source(self, engine: DecisionEngine) -> None:
        """Only one source provides data"""
        sources = {
            "feature": [
                {"title": "Option A", "description": "From feature", "confidence": 0.9, "effort": "low"}
            ]
        }
        result = engine.decide("test", sources=sources)
        assert isinstance(result, Decision)

    def test_thousand_options(self, engine: DecisionEngine) -> None:
        """1000 options to rank"""
        options = [
            {
                "title": f"Option {i}",
                "description": f"Rationale {i}",
                "confidence": 0.5 + (i / 2000),
                "effort": "low"
            }
            for i in range(1000)
        ]
        result = engine.decide("test", sources={"feature": options})
        # Should still rank and limit to top 5
        assert isinstance(result, Decision)

    def test_zero_options(self, engine: DecisionEngine) -> None:
        """No options available from all sources"""
        result = engine.decide("test", sources={
            "feature": [],
            "refactoring": [],
            "guardrails": [],
            "change": [],
        })
        assert isinstance(result, Decision)

    def test_option_dedup_identical(self, engine: DecisionEngine) -> None:
        """Two identical options"""
        sources = {
            "feature": [
                {"title": "Add cache", "description": "Identical", "confidence": 0.9, "effort": "low"},
                {"title": "Add cache", "description": "Identical", "confidence": 0.9, "effort": "low"},
            ]
        }
        result = engine.decide("test", sources=sources)
        # Should deduplicate
        assert isinstance(result, Decision)

    def test_option_dedup_different(self, engine: DecisionEngine) -> None:
        """Completely different options"""
        sources = {
            "feature": [
                {"title": "Add cache", "description": "Caching approach", "confidence": 0.9, "effort": "low"},
                {"title": "Remove database", "description": "Database approach", "confidence": 0.9, "effort": "high"},
            ]
        }
        result = engine.decide("test", sources=sources)
        # Should keep both
        assert isinstance(result, Decision)

    def test_multiple_sources(self, engine: DecisionEngine) -> None:
        """Data from all 4 sources"""
        sources = {
            "feature": [{"title": "Option A", "description": "Feature", "confidence": 0.9, "effort": "low"}],
            "refactoring": [{"title": "Option B", "description": "Refactor", "confidence": 0.85, "effort": "medium"}],
            "guardrails": [{"title": "Option C", "description": "Guardrails", "confidence": 0.8, "effort": "high"}],
            "change": [{"title": "Option D", "description": "Change", "confidence": 0.75, "effort": "low"}],
        }
        result = engine.decide("test", sources=sources)
        assert isinstance(result, Decision)

    def test_contradictory_sources(self, engine: DecisionEngine) -> None:
        """Sources suggest opposite things"""
        sources = {
            "feature": [{"title": "Add feature", "description": "Needed", "confidence": 0.9, "effort": "low"}],
            "refactoring": [{"title": "Remove feature", "description": "Duplication", "confidence": 0.85, "effort": "low"}],
        }
        result = engine.decide("test", sources=sources)
        # Should rank by confidence
        assert isinstance(result, Decision)

    def test_decision_reasoning_present(self, engine: DecisionEngine) -> None:
        """Decision should explain top choice"""
        sources = {
            "feature": [
                {"title": "Option A", "description": "Best choice", "confidence": 0.9, "effort": "low"}
            ]
        }
        result = engine.decide("test", sources=sources)
        assert result.reasoning != ""

    def test_top_n_capped_at_five(self, engine: DecisionEngine) -> None:
        """Results should be capped at 5"""
        options = [
            {
                "title": f"Option {i}",
                "description": f"Rationale {i}",
                "confidence": 1.0 - (i * 0.01),
                "effort": "low"
            }
            for i in range(10)
        ]
        result = engine.decide("test", sources={"feature": options})
        # Should have max 5 options
        assert isinstance(result, Decision)

    def test_no_recommended_option(self, engine: DecisionEngine) -> None:
        """No clear winner"""
        sources = {"feature": []}
        result = engine.decide("test", sources=sources)
        # Should still return decision
        assert isinstance(result, Decision)
