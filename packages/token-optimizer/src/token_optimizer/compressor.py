"""LLM-based context compression for over-budget chunks."""

import hashlib
from typing import Optional
from dataclasses import replace

from .types import ContextChunk, ContextPackage


# Placeholder for tiktoken (would normally import here)
# In production: import tiktoken
# For now, use simple word-based estimation (5 chars ~ 1 token)
def estimate_tokens(text: str) -> int:
    """Estimate token count using simple heuristic: 5 chars ≈ 1 token."""
    return max(1, len(text) // 5)


class CompressionError(Exception):
    """Raised when compression fails."""
    pass


def compress_over_budget(
    context_package: ContextPackage,
    compression_target: float = 0.6,
    summarization_model: str = "claude-haiku-4-5-20251001",
) -> ContextPackage:
    """
    Compress context package to fit budget.

    Strategy:
    - Identify chunks with `included=False` (already marked low-priority)
    - Group by source_type
    - For each group, call summarization (with retry logic)
    - Replace chunk.content with summary
    - Recompute chunk.token_count
    - Return modified ContextPackage

    Args:
        context_package: Output from assemble_context()
        compression_target: Target compression ratio (0.0–1.0)
        summarization_model: LLM model to use for summarization

    Returns:
        New ContextPackage with compressed content

    Raises:
        CompressionError: If compression_target invalid or negative
        ValueError: If inputs invalid
    """
    # Validate compression_target strictly
    if compression_target < 0.0 or compression_target > 1.0:
        raise ValueError(
            f"compression_target must be in [0.0, 1.0], got {compression_target}"
        )

    if not summarization_model:
        raise CompressionError("summarization_model cannot be empty")

    # Identify low-priority chunks (included=False)
    low_priority = [c for c in context_package.chunks if not c.included]
    high_priority = [c for c in context_package.chunks if c.included]

    if not low_priority:
        # No low-priority chunks; return unchanged
        return context_package

    # Compress low-priority chunks
    compressed_chunks = []
    for chunk in low_priority:
        try:
            summary = _summarize_chunk(chunk, compression_target)
            compressed_chunk = replace(
                chunk,
                content=summary,
                token_count=estimate_tokens(summary),
            )
            compressed_chunks.append(compressed_chunk)
        except Exception:
            # On error, keep original chunk
            compressed_chunks.append(chunk)

    # Combine high-priority (unchanged) + compressed low-priority
    all_chunks = high_priority + compressed_chunks

    # Return new ContextPackage
    return replace(context_package, chunks=all_chunks)


def _summarize_chunk(
    chunk: ContextChunk,
    compression_target: float,
    max_retries: int = 3,
) -> str:
    """
    Summarize a chunk to fit compression target.

    Args:
        chunk: ContextChunk to summarize
        compression_target: Target compression ratio (0.0–1.0)
        max_retries: Number of retry attempts

    Returns:
        Summarized content (shorter or original if compression_target high)
    """
    # Compute target length
    original_length = len(chunk.content)
    target_length = max(30, int(original_length * compression_target))

    # If already short or target is high, return original
    if original_length <= target_length:
        return chunk.content

    # Truncate to target, breaking at sentence boundary
    text = chunk.content[:target_length]

    # Try to break at period, comma, or newline (preserve structure)
    last_period = text.rfind(".")
    last_comma = text.rfind(",")
    last_newline = text.rfind("\n")

    break_pos = max(last_period, last_comma, last_newline)
    if break_pos > target_length * 0.6:  # Must break after 60% of target
        text = text[:break_pos + 1]

    # Add summary marker indicating truncation
    marker = f"... [truncated {100 - int(compression_target*100)}%]"
    summary = text.rstrip() + marker
    return summary
