"""Core ArtifactStore API: ingest, retrieve, search artifacts."""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from storage import OrthoDatabase

from .embedding import EmbeddingProvider, NullEmbedding
from .ingestion import ArtifactIngestionRequest, ValidationResult, validate_ingestion
from .versioning import make_artifact_id, make_content_hash, check_content_changed, get_next_version
from .search.bm25 import BM25Search
from .search.result import SearchResult


logger = logging.getLogger(__name__)


@dataclass
class Artifact:
    """Retrieved artifact with all metadata."""

    id: str
    repo_id: str
    type: str
    title: str
    content: str
    source: str
    created_at: str
    last_modified: str
    relevance_scope: str
    tags: list[str]
    related_symbols: list[str]
    estimated_tokens: int
    content_hash: str
    version: int


class ArtifactStore:
    """Main ContextHub API: ingest and retrieve artifacts."""

    def __init__(
        self,
        db: OrthoDatabase,
        repo_id: str,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.db = db
        # OrthoDatabase.connection() opens a NEW connection per call; grabbing a
        # fresh one per statement meant INSERTs and commit() ran on different
        # connections and writes were silently rolled back. Hold one connection.
        self._conn = db.connection()
        self.repo_id = repo_id
        self.embedding_provider = embedding_provider or NullEmbedding()
        self.vec_store = None

        # Initialize vector store if sqlite-vec available
        if self.embedding_provider.is_available and self.embedding_provider.embedding_dimension > 0:
            try:
                import sqlite_vec

                self.vec_store = self._init_vec_store()
            except ImportError:
                logger.warning("sqlite-vec not available, semantic search disabled")

    def _init_vec_store(self):
        """Initialize vector store for embedding storage."""
        # Placeholder; full implementation in semantic search module
        return None

    def ingest_artifact(self, req: ArtifactIngestionRequest) -> str:
        """
        Synchronous artifact ingestion. Returns artifact_id immediately.

        Raises:
            ValidationError: If request invalid
        """
        # Validate request
        validation = validate_ingestion(req)
        if not validation.is_valid:
            raise ValueError(f"Artifact validation failed: {validation.errors}")

        # Generate content hash and artifact ID
        content_hash = make_content_hash(req.content)
        artifact_id = make_artifact_id(self.repo_id, req.title, req.source, content_hash)

        # Check if content changed (for versioning)
        content_changed = check_content_changed(self._conn, artifact_id, content_hash)

        if not content_changed:
            # Content unchanged, return existing artifact_id
            return artifact_id

        # Determine version number
        if content_changed and self._conn.execute(
            "SELECT COUNT(*) FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()[0] > 0:
            next_version = get_next_version(self._conn, artifact_id)
        else:
            next_version = 1

        # Estimate token count (simple: word count / 0.25 tokens per word)
        estimated_tokens = int(len(req.content.split()) / 0.25)

        # Insert artifact (synchronous, blocking)
        now = datetime.now().isoformat()
        self._conn.execute(
            """
            INSERT INTO artifacts
            (id, repo_id, type, title, content, source, created_at, last_modified,
             relevance_scope, tags, related_symbols, estimated_tokens, content_hash, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                self.repo_id,
                req.type,
                req.title,
                req.content,
                req.source,
                now,
                now,
                req.relevance_scope,
                json.dumps(req.tags),
                json.dumps(req.related_symbols or []),
                estimated_tokens,
                content_hash,
                next_version,
            ),
        )
        self._conn.commit()

        # FTS5 automatically synced by trigger (no explicit code needed)

        # Schedule embedding computation (non-blocking)
        self._compute_embedding_async(artifact_id, req.content, req.type)

        return artifact_id

    def _compute_embedding_async(self, artifact_id: str, content: str, artifact_type: str) -> None:
        """Non-blocking embedding computation. Errors logged but not raised."""
        try:
            if self.embedding_provider and self.embedding_provider.is_available:
                embedding = self.embedding_provider.embed(content, artifact_type)
                if embedding and self.vec_store:
                    self.vec_store.upsert(artifact_id, embedding)
        except Exception as e:
            logger.warning(f"Failed to embed artifact {artifact_id}: {e}")

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve latest version of artifact by ID."""
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE id = ? ORDER BY version DESC LIMIT 1",
            (artifact_id,),
        ).fetchone()

        return self._row_to_artifact(row) if row else None

    def get_artifact_version(self, artifact_id: str, version: int) -> Optional[Artifact]:
        """Retrieve specific version of artifact."""
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE id = ? AND version = ?",
            (artifact_id, version),
        ).fetchone()

        return self._row_to_artifact(row) if row else None

    def get_artifact_history(self, artifact_id: str) -> list[Artifact]:
        """Retrieve all versions of artifact (audit trail)."""
        rows = self._conn.execute(
            "SELECT * FROM artifacts WHERE id = ? ORDER BY version ASC",
            (artifact_id,),
        ).fetchall()

        return [self._row_to_artifact(row) for row in rows if row]

    def delete_artifact(self, artifact_id: str) -> None:
        """Soft delete artifact (remove from database)."""
        self._conn.execute(
            "DELETE FROM artifacts WHERE id = ?", (artifact_id,)
        )
        self._conn.commit()

    def search(
        self,
        query: str,
        artifact_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        """Search artifacts by keyword using BM25 ranking."""
        searcher = BM25Search(self._conn)
        type_filter = [artifact_type] if artifact_type else None
        return searcher.search(query, limit=limit, type_filter=type_filter)

    @staticmethod
    def _row_to_artifact(row) -> Optional[Artifact]:
        """Convert database row to Artifact dataclass."""
        if not row:
            return None

        return Artifact(
            id=row[0],
            repo_id=row[2],
            type=row[3],
            title=row[4],
            content=row[5],
            source=row[6],
            created_at=row[7],
            last_modified=row[8],
            relevance_scope=row[9],
            tags=json.loads(row[10]) if row[10] else [],
            related_symbols=json.loads(row[11]) if row[11] else [],
            estimated_tokens=row[12],
            content_hash=row[13],
            version=row[1],
        )
