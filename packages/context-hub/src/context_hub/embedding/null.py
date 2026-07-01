"""No-op embedding provider (default, Phase 1)."""

from .provider import EmbeddingProvider


class NullEmbedding(EmbeddingProvider):
    """No-op embedding provider. Used when embeddings are disabled."""

    def embed(self, text: str, artifact_type: str) -> list[float] | None:
        """Return None (no embedding computed)."""
        return None

    @property
    def embedding_dimension(self) -> int:
        """Null provider has no dimension."""
        return 0

    @property
    def is_available(self) -> bool:
        """Null provider is always available."""
        return True
