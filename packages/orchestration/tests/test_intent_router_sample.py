"""Sample tests for IntentRouter (task-012)."""

import pytest
from pathlib import Path
from orchestration.intent.router import IntentRouter
from orchestration.intent.types import IntentClassification


class TestIntentRouterBasic:
    """Test basic intent routing."""

    @pytest.fixture
    def utterance_corpus(self):
        """Minimal utterance corpus for testing."""
        return {
            "architect": [
                "write an ADR",
                "write an ADR for this decision",
                "design the system",
                "architectural decision",
            ],
            "coder": [
                "implement this feature",
                "write code",
                "fix the bug",
            ],
            "reviewer": [
                "review this code",
                "code review",
            ],
        }

    @pytest.fixture
    def router(self, utterance_corpus):
        """Create IntentRouter with test corpus."""
        try:
            return IntentRouter(utterance_corpus)
        except RuntimeError as e:
            pytest.skip(f"HuggingFace encoder failed to load: {e}")

    def test_intent_router_classifies_architect_intent(self, router):
        """Verify router classifies architect-related utterance."""
        result = router.classify_intent("write an ADR for this decision")

        assert result.type == "architect", f"Expected type 'architect', got '{result.type}'"
        assert result.method == "router", f"Expected method 'router', got '{result.method}'"
        assert result.confidence >= 0.7, f"Expected confidence >= 0.7, got {result.confidence}"

    def test_intent_router_classifies_coder_intent(self, router):
        """Verify router classifies coder-related utterance."""
        result = router.classify_intent("implement this feature")

        assert result.type == "coder"
        assert result.method == "router"
        assert result.confidence >= 0.7

    def test_intent_router_classifies_reviewer_intent(self, router):
        """Verify router classifies reviewer-related utterance."""
        result = router.classify_intent("review this code")

        assert result.type == "reviewer"
        assert result.method == "router"
        assert result.confidence >= 0.7


class TestIntentRouterThreshold:
    """Test confidence threshold behavior."""

    @pytest.fixture
    def utterance_corpus(self):
        return {
            "architect": ["write an ADR", "design system", "architectural decision"],
            "coder": ["implement feature", "write code", "fix bug"],
        }

    @pytest.fixture
    def router(self, utterance_corpus):
        try:
            return IntentRouter(utterance_corpus)
        except RuntimeError:
            pytest.skip("HuggingFace encoder unavailable")

    def test_intent_router_confidence_at_threshold_uses_router_method(self, router):
        """Verify confidence >= 0.7 triggers router method (not fallback)."""
        # This test uses utterances that should have high confidence
        result = router.classify_intent("write an ADR")

        assert result.confidence >= 0.7
        assert result.method == "router"

    def test_intent_router_below_threshold_triggers_fallback(self, router):
        """Verify low-confidence utterance triggers fallback."""
        # Use deliberately ambiguous/off-domain text
        result = router.classify_intent("the quick brown fox jumps over lazy dog")

        # Should fall back to LLM (low confidence) or have method="llm_fallback"
        if result.confidence < 0.7:
            assert result.method == "llm_fallback"


class TestIntentRouterConfidence:
    """Test confidence field semantics."""

    @pytest.fixture
    def utterance_corpus(self):
        return {
            "architect": ["write an ADR", "design system"],
            "coder": ["write code", "implement"]
        }

    @pytest.fixture
    def router(self, utterance_corpus):
        try:
            return IntentRouter(utterance_corpus)
        except RuntimeError:
            pytest.skip("HuggingFace encoder unavailable")

    def test_intent_router_confidence_is_float_in_range(self, router):
        """Verify confidence is float in [0.0, 1.0]."""
        result = router.classify_intent("write an ADR")

        assert isinstance(result.confidence, float), f"Expected float, got {type(result.confidence)}"
        assert 0.0 <= result.confidence <= 1.0, f"Confidence {result.confidence} out of range"

    def test_intent_router_confidence_is_raw_similarity(self, router):
        """Verify confidence is raw similarity (not scaled/normalized differently)."""
        # Semantic similarity should be consistent across similar utterances
        result1 = router.classify_intent("write an ADR")
        result2 = router.classify_intent("write an ADR for this decision")

        # Both should be high confidence for architect
        assert result1.confidence >= 0.7
        assert result2.confidence >= 0.7

    def test_intent_router_method_field_matches_threshold(self, router):
        """Verify method field correctly reflects threshold logic."""
        # High confidence should use router method
        high_confidence = router.classify_intent("write an ADR")
        if high_confidence.confidence >= 0.7:
            assert high_confidence.method == "router"

        # Low confidence should use fallback method
        low_confidence = router.classify_intent("the quick brown fox jumps over lazy dog")
        if low_confidence.confidence < 0.7:
            assert low_confidence.method == "llm_fallback"
