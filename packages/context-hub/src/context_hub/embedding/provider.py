"""Abstract embedding provider interface."""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstraction for embedding computation. Implementations handle specific providers."""

    @abstractmethod
    def embed(self, text: str, artifact_type: str) -> list[float] | None:
        """
        Compute embedding for text.

        Args:
            text: Content to embed
            artifact_type: Type of artifact (frd, adr, code, etc.) for provider optimization

        Returns:
            list of floats (embedding vector), or None if embedding fails

        Raises:
            Should not raise; return None on failure for graceful degradation
        """
        ...

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings from this provider."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is ready to use."""
        ...
