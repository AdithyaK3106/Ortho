"""Focused integration tests for Context Compressor (Component 4)."""

import pytest
from token_optimizer.compressor import compress_over_budget, CompressionError, estimate_tokens
from token_optimizer.types import ContextChunk, ContextPackage
from token_optimizer.budget import TokenBudget


def make_chunk(cid: str, content: str, tokens: int = 100, score: float = 0.5, included: bool = False):
    return ContextChunk(
        id=cid,
        source_type="artifact",
        source_id=f"src_{cid}",
        content=content,
        relevance_score=score,
        token_count=tokens,
        included=included,
    )


def make_package(chunks, budget_total=8000):
    return ContextPackage(
        id="pkg1",
        workflow_run_id="wf1",
        step_id="step1",
        chunks=chunks,
        budget=TokenBudget(total=budget_total, used=0, model="test"),
        assembled_at="2026-01-01T00:00:00Z",
    )


class TestCompressorValidation:
    """Test input validation."""

    def test_invalid_compression_target_negative(self):
        """Negative compression target raises ValueError."""
        pkg = make_package([make_chunk("c1", "text", included=False)])
        with pytest.raises(ValueError):
            compress_over_budget(pkg, compression_target=-0.1)

    def test_invalid_compression_target_too_high(self):
        """Compression target > 1.0 raises ValueError."""
        pkg = make_package([make_chunk("c1", "text", included=False)])
        with pytest.raises(ValueError):
            compress_over_budget(pkg, compression_target=1.5)

    def test_valid_compression_targets_0_and_1(self):
        """Compression targets 0.0 and 1.0 are valid."""
        pkg = make_package([make_chunk("c1", "text", included=False)])
        # Should not raise
        compress_over_budget(pkg, compression_target=0.0)
        compress_over_budget(pkg, compression_target=1.0)


class TestCompressorBasic:
    """Basic compression behavior."""

    def test_no_low_priority_chunks(self):
        """All high-priority chunks → return unchanged."""
        chunks = [
            make_chunk("c1", "content1", included=True),
            make_chunk("c2", "content2", included=True),
        ]
        pkg = make_package(chunks)
        result = compress_over_budget(pkg, compression_target=0.5)
        assert len(result.chunks) == 2
        # Chunks should be unchanged (not compressed)
        assert result.chunks[0].content == "content1"

    def test_compress_low_priority(self):
        """Low-priority chunks are compressed."""
        chunks = [
            make_chunk("c1", "This is a long content" * 10, tokens=500, included=False),
        ]
        pkg = make_package(chunks)
        result = compress_over_budget(pkg, compression_target=0.5)
        # Content should be shorter
        assert len(result.chunks[0].content) < len(chunks[0].content)

    def test_mixed_high_low_priority(self):
        """High-priority kept, low-priority compressed."""
        chunks = [
            make_chunk("high", "keep this", included=True),
            make_chunk("low", "long content" * 50, tokens=1000, included=False),
        ]
        pkg = make_package(chunks)
        result = compress_over_budget(pkg, compression_target=0.3)

        # High-priority preserved
        assert result.chunks[0].id == "high"
        assert result.chunks[0].content == "keep this"

        # Low-priority compressed
        assert result.chunks[1].id == "low"
        assert len(result.chunks[1].content) < len(chunks[1].content)


class TestCompressorTokenCounting:
    """Token recount after compression."""

    def test_token_count_reduced_after_compression(self):
        """Compressed content has lower token count."""
        chunks = [make_chunk("c1", "word " * 100, tokens=200, included=False)]
        pkg = make_package(chunks)
        result = compress_over_budget(pkg, compression_target=0.5)

        # Token count should be lower (roughly 50% of original)
        assert result.chunks[0].token_count < chunks[0].token_count

    def test_token_estimate_function(self):
        """estimate_tokens gives reasonable counts."""
        # 5 chars ≈ 1 token
        tokens = estimate_tokens("hello world test")
        assert tokens >= 2 and tokens <= 4


class TestCompressorErrorHandling:
    """Error handling and edge cases."""

    def test_empty_package(self):
        """Empty package handled gracefully."""
        pkg = make_package([])
        result = compress_over_budget(pkg, compression_target=0.5)
        assert len(result.chunks) == 0

    def test_all_high_priority(self):
        """All high-priority chunks → no compression."""
        chunks = [
            make_chunk("c1", "content1", included=True),
            make_chunk("c2", "content2", included=True),
        ]
        pkg = make_package(chunks)
        result = compress_over_budget(pkg, compression_target=0.1)
        # Nothing to compress
        assert result.chunks[0].content == chunks[0].content
        assert result.chunks[1].content == chunks[1].content

    def test_invalid_model_name(self):
        """Invalid model string raises error."""
        pkg = make_package([make_chunk("c1", "text", included=False)])
        with pytest.raises(CompressionError):
            compress_over_budget(pkg, summarization_model="")


class TestCompressorDeterminism:
    """Deterministic behavior (same input → same output)."""

    def test_deterministic_compression(self):
        """Same input produces same output."""
        chunks = [make_chunk("c1", "content" * 50, tokens=500, included=False)]
        pkg = make_package(chunks)

        result1 = compress_over_budget(pkg, compression_target=0.4)
        result2 = compress_over_budget(pkg, compression_target=0.4)

        assert result1.chunks[0].content == result2.chunks[0].content
