"""Embedding provider abstraction."""

from .null import NullEmbedding
from .provider import EmbeddingProvider

__all__ = ["EmbeddingProvider", "NullEmbedding"]
