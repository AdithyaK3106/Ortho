"""Intent-aware reranking of context chunks."""

from dataclasses import dataclass, replace
from typing import Dict, List
from .types import ContextChunk


@dataclass
class RerankerConfig:
    """Configuration for intent-aware reranking."""

    # Boost factors per intent class (0.0–2.0 multiplier on relevance_score)
    feature_development_boosts: Dict[str, float]
    bug_fix_boosts: Dict[str, float]
    refactor_boosts: Dict[str, float]
    analysis_boosts: Dict[str, float]

    @staticmethod
    def default() -> "RerankerConfig":
        """Default reranker configuration."""
        return RerankerConfig(
            feature_development_boosts={
                "api": 1.8,
                "interface": 1.8,
                "public": 1.7,
                "example": 1.6,
                "export": 1.5,
                "function": 1.3,
                "class": 1.3,
            },
            bug_fix_boosts={
                "error": 1.8,
                "exception": 1.8,
                "test": 1.7,
                "edge": 1.6,
                "fix": 1.5,
                "bug": 1.5,
                "assert": 1.4,
            },
            refactor_boosts={
                "dependency": 1.8,
                "import": 1.7,
                "coupling": 1.7,
                "metric": 1.6,
                "circula": 1.6,  # "circular" prefix
                "refactor": 1.5,
                "module": 1.4,
            },
            analysis_boosts={
                "architecture": 1.8,
                "metric": 1.7,
                "summary": 1.6,
                "design": 1.5,
                "pattern": 1.5,
                "structure": 1.4,
            },
        )


def _extract_boost_keywords(
    chunk: ContextChunk,
    boost_keywords: Dict[str, float],
) -> float:
    """
    Extract maximum boost factor from chunk keywords.

    Scans chunk content and metadata for keyword matches.
    Returns highest matching boost factor (1.0 if no match).
    """
    content_lower = chunk.content.lower()

    # Check each keyword; keep track of max boost
    max_boost = 1.0

    for keyword, boost_factor in boost_keywords.items():
        if keyword in content_lower:
            max_boost = max(max_boost, boost_factor)

    return max_boost


def rerank_by_intent(
    chunks: List[ContextChunk],
    intent: str,
    intent_class: str,
    config: RerankerConfig | None = None,
) -> List[ContextChunk]:
    """
    Rerank chunks based on intent relevance.

    Strategy:
    - Parse intent class (feature_development, bug_fix, refactor, analysis)
    - Look up boost keywords for that intent class
    - For each chunk, scan content for keywords and extract boost factor
    - Multiply chunk.relevance_score by boost factor
    - Resort by new relevance_score (descending), breaking ties by chunk.id

    Args:
        chunks: Already deduplicated chunks
        intent: User's raw intent string (for future ML-based ranking if needed)
        intent_class: Output from intent router (feature_development, bug_fix, etc.)
        config: Reranker config (uses default if None)

    Returns:
        Same chunks, relevance_score modified, resorted by score descending
    """
    if config is None:
        config = RerankerConfig.default()

    # Select boost keywords based on intent class
    boost_keywords: Dict[str, float] = {}
    if intent_class == "feature_development":
        boost_keywords = config.feature_development_boosts
    elif intent_class == "bug_fix":
        boost_keywords = config.bug_fix_boosts
    elif intent_class == "refactor":
        boost_keywords = config.refactor_boosts
    elif intent_class == "analysis":
        boost_keywords = config.analysis_boosts
    # else: no boost keywords, all chunks get 1.0x multiplier

    # Rerank each chunk
    reranked = []
    for chunk in chunks:
        boost_factor = _extract_boost_keywords(chunk, boost_keywords)
        new_score = chunk.relevance_score * boost_factor

        # Create modified chunk with new score
        reranked_chunk = replace(chunk, relevance_score=new_score)
        reranked.append(reranked_chunk)

    # Resort by relevance_score (descending), then by chunk.id (ascending for stability)
    reranked.sort(key=lambda c: (-c.relevance_score, c.id))

    return reranked
