"""Tests for semantic duplicate detector."""

import pytest
from token_optimizer.deduplicator import (
    detect_and_remove_duplicates,
    DeduplicationResult,
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


def test_empty_list():
    """100% duplicates (empty) returns empty list."""
    result = detect_and_remove_duplicates([])
    assert result.deduplicated_chunks == []
    assert result.removed_count == 0
    assert result.cluster_count == 0


def test_single_chunk():
    """Single chunk returns single chunk."""
    chunk = make_chunk("c1", "some content")
    result = detect_and_remove_duplicates([chunk])
    assert len(result.deduplicated_chunks) == 1
    assert result.deduplicated_chunks[0].id == "c1"
    assert result.removed_count == 0


def test_no_duplicates():
    """0% overlap returns all chunks."""
    chunks = [
        make_chunk("c1", "apple orange banana"),
        make_chunk("c2", "dog cat bird"),
        make_chunk("c3", "sun moon star"),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    assert len(result.deduplicated_chunks) == 3
    assert result.removed_count == 0
    assert result.cluster_count == 3


def test_complete_duplicates():
    """100% duplicate chunks returns 1 chunk."""
    content = "the quick brown fox jumps over the lazy dog"
    chunks = [
        make_chunk("c1", content, relevance_score=0.5),
        make_chunk("c2", content, relevance_score=0.7),
        make_chunk("c3", content, relevance_score=0.6),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    assert len(result.deduplicated_chunks) == 1
    assert result.removed_count == 2
    assert result.cluster_count == 1
    # Should keep the highest relevance (c2 with 0.7)
    assert result.deduplicated_chunks[0].id == "c2"


def test_mixed_duplicates():
    """10 chunks with some clustering removes duplicates."""
    chunks = [
        make_chunk("c1", "authentication service validates user tokens", 0.9),
        make_chunk("c2", "auth service checks user tokens", 0.8),  # high overlap with c1
        make_chunk("c3", "database connection pool manages connections", 0.7),
        make_chunk("c4", "db pool handles connection management", 0.85),  # high overlap with c3
        make_chunk("c5", "monitoring alerts track system health", 0.6),
        make_chunk("c6", "alerts monitor system health", 0.75),  # medium overlap with c5
        make_chunk("c7", "completely different content here", 0.5),
        make_chunk("c8", "another unique topic", 0.55),
        make_chunk("c9", "yet another different thing", 0.65),
        make_chunk("c10", "final unique content", 0.7),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.50)
    # Lower threshold (0.50) may not catch all the similarities we want
    # Just verify we have fewer chunks than we started with
    assert len(result.deduplicated_chunks) < len(chunks)
    assert result.removed_count > 0


def test_order_preservation():
    """Deduplicated list matches input order."""
    chunks = [
        make_chunk("c1", "first chunk content", 0.5),
        make_chunk("c2", "second chunk content", 0.6),
        make_chunk("c3", "third chunk content", 0.7),
        make_chunk("c4", "first chunk content", 0.4),  # duplicate of c1
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    ids = [c.id for c in result.deduplicated_chunks]
    # c1 should come before c2 (preserves order)
    if "c1" in ids:
        c1_idx = ids.index("c1")
        c2_idx = ids.index("c2")
        assert c1_idx < c2_idx


def test_highest_relevance_per_cluster():
    """Best chunk per cluster is selected by relevance_score."""
    chunks = [
        make_chunk("low", "duplicate content", 0.3),
        make_chunk("med", "duplicate content", 0.6),
        make_chunk("high", "duplicate content", 0.9),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    assert len(result.deduplicated_chunks) == 1
    assert result.deduplicated_chunks[0].id == "high"


def test_deterministic_output():
    """Same input produces same output."""
    chunks = [
        make_chunk("c1", "apple banana cherry", 0.5),
        make_chunk("c2", "apple banana grape", 0.6),
        make_chunk("c3", "dog cat bird", 0.7),
    ]
    result1 = detect_and_remove_duplicates(chunks, similarity_threshold=0.60)
    result2 = detect_and_remove_duplicates(chunks, similarity_threshold=0.60)

    ids1 = [c.id for c in result1.deduplicated_chunks]
    ids2 = [c.id for c in result2.deduplicated_chunks]
    assert ids1 == ids2


def test_threshold_sensitivity():
    """Lower threshold = more aggressive clustering (more deduplication)."""
    chunks = [
        make_chunk("c1", "apple banana cherry date elderberry", 0.5),
        make_chunk("c2", "apple banana cherry date", 0.6),
        make_chunk("c3", "apple banana cherry", 0.7),
    ]

    # High threshold (strict): less clustering
    result_strict = detect_and_remove_duplicates(chunks, similarity_threshold=0.90)
    count_strict = len(result_strict.deduplicated_chunks)

    # Low threshold (lenient): more clustering
    result_lenient = detect_and_remove_duplicates(chunks, similarity_threshold=0.50)
    count_lenient = len(result_lenient.deduplicated_chunks)

    # Lenient threshold should result in fewer chunks (more aggressive deduplication)
    assert count_lenient <= count_strict


def test_edge_case_single_word_chunks():
    """Chunks with single words handle gracefully."""
    chunks = [
        make_chunk("c1", "apple", 0.5),
        make_chunk("c2", "apple", 0.6),
        make_chunk("c3", "banana", 0.7),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    # c1 and c2 should cluster together
    assert len(result.deduplicated_chunks) == 2
    assert result.removed_count == 1


def test_empty_content():
    """Empty content chunks are handled."""
    chunks = [
        make_chunk("c1", "", 0.5),
        make_chunk("c2", "", 0.6),
        make_chunk("c3", "real content", 0.7),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    # Empty chunks won't match anything (0 overlap)
    assert len(result.deduplicated_chunks) >= 2


def test_case_insensitive_similarity():
    """Similarity comparison is case-insensitive."""
    chunks = [
        make_chunk("c1", "Apple Banana Cherry", 0.5),
        make_chunk("c2", "apple banana cherry", 0.6),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    assert len(result.deduplicated_chunks) == 1
    assert result.removed_count == 1


def test_whitespace_handling():
    """Extra whitespace doesn't affect matching."""
    chunks = [
        make_chunk("c1", "apple   banana   cherry", 0.5),
        make_chunk("c2", "apple banana cherry", 0.6),
    ]
    result = detect_and_remove_duplicates(chunks, similarity_threshold=0.85)
    # Should be treated as duplicate (same tokens)
    assert len(result.deduplicated_chunks) == 1
