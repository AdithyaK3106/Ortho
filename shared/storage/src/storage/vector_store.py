from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class SearchResult:
    id: str
    distance: float
    metadata: dict


class VectorStore:
    """sqlite-vec wrapper for embedding storage and KNN search."""

    def upsert(self, id: str, embedding: list[float], metadata: dict) -> None:
        """Insert or update an embedding with metadata."""
        pass

    def search(
        self, query_embedding: list[float], k: int, filter: Optional[dict] = None
    ) -> list[SearchResult]:
        """Search for k nearest neighbors matching query embedding."""
        return []

    def delete(self, id: str) -> None:
        """Delete an embedding by ID."""
        pass
