"""Tests for intent-aware reranker."""

import pytest
from token_optimizer.reranker import (
    rerank_by_intent,
    RerankerConfig,
    _extract_boost_keywords,
)
from token_optimizer.types import ContextChunk


def make_chunk(
    chunk_id: str,
    content: str,
    relevance_score: float = 0.5,
    token_count: int = 100,
) -> ContextChunk:
    """Helper to create a ContextChunk."""
    return ContextChunk(
        id=chunk_id,
        source_type="artifact",
        source_id=f"source_{chunk_id}",
        content=content,
        relevance_score=relevance_score,
        token_count=token_count,
        included=True,
    )


class TestExtractBoostKeywords:
    """Test keyword extraction for boosts."""

    def test_single_matching_keyword(self):
        """Single matching keyword returns boost factor."""
        config = RerankerConfig.default()
        chunk = make_chunk("c1", "This is a public interface")

        boost = _extract_boost_keywords(chunk, config.feature_development_boosts)
        # "public" (1.7) and "interface" (1.8) both match; max is 1.8
        assert boost == 1.8

    def test_multiple_matching_keywords_returns_max(self):
        """Multiple keywords return max boost factor."""
        config = RerankerConfig.default()
        chunk = make_chunk(
            "c1", "This API is a public interface for external clients"
        )

        boost = _extract_boost_keywords(chunk, config.feature_development_boosts)
        # "public" (1.7), "api" (1.8), "interface" (1.8)
        assert boost == 1.8

    def test_no_matching_keywords_returns_1(self):
        """No matching keywords returns 1.0 (no boost)."""
        config = RerankerConfig.default()
        chunk = make_chunk("c1", "Some random implementation detail")

        boost = _extract_boost_keywords(chunk, config.feature_development_boosts)
        assert boost == 1.0

    def test_keyword_matching_is_case_insensitive(self):
        """Keyword matching is case-insensitive."""
        config = RerankerConfig.default()
        chunk = make_chunk("c1", "This is a PUBLIC INTERFACE")

        boost = _extract_boost_keywords(chunk, config.feature_development_boosts)
        # Both "public" (1.7) and "interface" (1.8) match; max is 1.8
        assert boost == 1.8


class TestRerankerByIntent:
    """Test intent-aware reranker."""

    def test_feature_development_boosts_api_chunks(self):
        """Feature development intent boosts API and interface chunks."""
        chunks = [
            make_chunk("c1", "database connection pool", 0.5),
            make_chunk("c2", "public API endpoint for authentication", 0.5),
        ]

        reranked = rerank_by_intent(chunks, "add feature X", "feature_development")

        # c2 should be first (API boost applied)
        assert reranked[0].id == "c2"
        assert reranked[0].relevance_score > reranked[1].relevance_score

    def test_bug_fix_boosts_error_chunks(self):
        """Bug fix intent boosts error and test chunks."""
        chunks = [
            make_chunk("c1", "general implementation code", 0.5),
            make_chunk("c2", "error handling for null values", 0.5),
            make_chunk("c3", "test cases for edge conditions", 0.5),
        ]

        reranked = rerank_by_intent(chunks, "fix null pointer bug", "bug_fix")

        # c2 and c3 should be boosted; check c2 has higher score than c1
        scores = {c.id: c.relevance_score for c in reranked}
        assert scores["c2"] > scores["c1"]
        assert scores["c3"] > scores["c1"]

    def test_refactor_boosts_dependency_chunks(self):
        """Refactor intent boosts dependency and coupling chunks."""
        chunks = [
            make_chunk("c1", "basic function implementation", 0.5),
            make_chunk("c2", "dependency imports and coupling", 0.5),
            make_chunk("c3", "circular dependency detection", 0.5),
        ]

        reranked = rerank_by_intent(chunks, "reduce coupling", "refactor")

        scores = {c.id: c.relevance_score for c in reranked}
        assert scores["c2"] > scores["c1"]
        assert scores["c3"] > scores["c1"]

    def test_analysis_boosts_architecture_chunks(self):
        """Analysis intent boosts architecture and design chunks."""
        chunks = [
            make_chunk("c1", "implementation detail", 0.5),
            make_chunk("c2", "architecture design pattern", 0.5),
            make_chunk("c3", "system structure overview", 0.5),
        ]

        reranked = rerank_by_intent(chunks, "what is the architecture", "analysis")

        scores = {c.id: c.relevance_score for c in reranked}
        assert scores["c2"] > scores["c1"]
        assert scores["c3"] > scores["c1"]

    def test_unknown_intent_class_no_boost(self):
        """Unknown intent class applies no boosts (1.0x multiplier)."""
        chunks = [
            make_chunk("c1", "public API endpoint", 0.5),
            make_chunk("c2", "internal implementation", 0.4),
        ]

        reranked = rerank_by_intent(chunks, "do something", "unknown_intent")

        # c1 should still be first (higher original relevance), no boosts applied
        scores = {c.id: c.relevance_score for c in reranked}
        assert scores["c1"] == 0.5
        assert scores["c2"] == 0.4

    def test_resort_by_score_descending(self):
        """Reranked chunks sorted by score descending."""
        chunks = [
            make_chunk("c1", "implementation", 0.2),  # low baseline
            make_chunk("c2", "public API", 0.3),  # boost 1.8x -> 0.54
            make_chunk("c3", "internal code", 0.4),
        ]

        reranked = rerank_by_intent(chunks, "add feature", "feature_development")

        # c2 should be first after boosting (0.54 > 0.4 > 0.2)
        assert reranked[0].id == "c2"

    def test_tie_breaking_by_id(self):
        """Ties in relevance score broken by chunk ID (stable sort)."""
        chunks = [
            make_chunk("c1", "api", 0.5),
            make_chunk("c2", "api", 0.5),  # same content, same score
        ]

        reranked = rerank_by_intent(chunks, "add feature", "feature_development")

        # Both get same boost, tie broken by ID
        scores = [c.relevance_score for c in reranked]
        assert scores[0] == scores[1]
        # Stable sort: c1 comes before c2 alphabetically
        assert reranked[0].id < reranked[1].id

    def test_deterministic_output(self):
        """Same input produces same output."""
        chunks = [
            make_chunk("c1", "implementation", 0.5),
            make_chunk("c2", "public API", 0.6),
            make_chunk("c3", "internal", 0.4),
        ]

        result1 = rerank_by_intent(chunks, "add feature", "feature_development")
        result2 = rerank_by_intent(chunks, "add feature", "feature_development")

        ids1 = [c.id for c in result1]
        ids2 = [c.id for c in result2]
        assert ids1 == ids2

    def test_original_chunks_not_modified(self):
        """Original chunks list is not modified in-place."""
        chunks = [
            make_chunk("c1", "implementation", 0.5),
            make_chunk("c2", "public API", 0.6),
        ]
        original_ids = [c.id for c in chunks]

        reranked = rerank_by_intent(chunks, "add feature", "feature_development")

        # Original list unchanged
        assert [c.id for c in chunks] == original_ids
        # But reranked list is different
        assert [c.id for c in reranked] != original_ids

    def test_boost_multiplies_score(self):
        """Boost factor correctly multiplies relevance score."""
        chunk = make_chunk("c1", "error handling", 0.5)
        config = RerankerConfig.default()

        reranked = rerank_by_intent([chunk], "fix bug", "bug_fix", config=config)

        # "error" has boost 1.8 in bug_fix
        expected_score = 0.5 * 1.8
        assert reranked[0].relevance_score == pytest.approx(expected_score)

    def test_multiple_keywords_max_boost_applied(self):
        """When chunk has multiple keywords, max boost is applied."""
        chunk = make_chunk("c1", "error handling with exception catch", 0.5)
        config = RerankerConfig.default()

        reranked = rerank_by_intent([chunk], "fix bug", "bug_fix", config=config)

        # "error" (1.8), "exception" (1.8), "catch" (no match)
        # Should use max = 1.8
        expected_score = 0.5 * 1.8
        assert reranked[0].relevance_score == pytest.approx(expected_score)

    def test_empty_chunks_list(self):
        """Empty chunks list returns empty list."""
        reranked = rerank_by_intent([], "add feature", "feature_development")
        assert reranked == []

    def test_custom_config(self):
        """Custom config is used instead of default."""
        chunks = [make_chunk("c1", "custom_keyword", 0.5)]

        custom_config = RerankerConfig(
            feature_development_boosts={"custom_keyword": 2.0},
            bug_fix_boosts={},
            refactor_boosts={},
            analysis_boosts={},
        )

        reranked = rerank_by_intent(
            chunks, "add feature", "feature_development", config=custom_config
        )

        assert reranked[0].relevance_score == pytest.approx(0.5 * 2.0)


class TestRerankerConfig:
    """Test RerankerConfig default values."""

    def test_default_config_has_all_intent_classes(self):
        """Default config has boosts for all intent classes."""
        config = RerankerConfig.default()
        assert config.feature_development_boosts
        assert config.bug_fix_boosts
        assert config.refactor_boosts
        assert config.analysis_boosts

    def test_default_config_boost_factors_reasonable(self):
        """Default config boost factors are in reasonable range (1.0-2.0)."""
        config = RerankerConfig.default()

        for intent_boosts in [
            config.feature_development_boosts,
            config.bug_fix_boosts,
            config.refactor_boosts,
            config.analysis_boosts,
        ]:
            for boost_factor in intent_boosts.values():
                assert 1.0 <= boost_factor <= 2.0
