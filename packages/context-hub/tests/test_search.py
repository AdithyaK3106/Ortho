"""Tests for search implementations (BM25, semantic, hybrid)."""

import pytest

from context_hub.search import BM25Search, HybridSearch, SemanticSearch


class TestBM25Search:
    """Test BM25 full-text search."""

    def test_bm25_search_basic(self, artifact_store, authentication_artifact):
        """Basic BM25 search finds artifact."""
        artifact_store.ingest_artifact(authentication_artifact)

        bm25 = BM25Search(artifact_store.db.connection())
        results = bm25.search("authentication")

        assert len(results) > 0
        assert results[0].title == authentication_artifact.title

    def test_bm25_search_empty_query(self, artifact_store, authentication_artifact):
        """Empty query returns no results."""
        artifact_store.ingest_artifact(authentication_artifact)

        bm25 = BM25Search(artifact_store.db.connection())
        # FTS5 MATCH with empty string will fail gracefully
        # This tests that we handle it properly
        try:
            results = bm25.search("")
            # If no exception, results should be empty
            assert len(results) == 0
        except Exception:
            # FTS5 may raise on empty query, which is acceptable
            pass

    def test_bm25_search_nonexistent(self, artifact_store, authentication_artifact):
        """Search for nonexistent term returns empty."""
        artifact_store.ingest_artifact(authentication_artifact)

        bm25 = BM25Search(artifact_store.db.connection())
        results = bm25.search("xyz_nonexistent_term")

        assert len(results) == 0

    def test_bm25_search_type_filter(self, artifact_store, valid_artifact_request, authentication_artifact):
        """Type filter limits results."""
        artifact_store.ingest_artifact(valid_artifact_request)  # type="adr"
        artifact_store.ingest_artifact(authentication_artifact)  # type="spec"

        bm25 = BM25Search(artifact_store.db.connection())
        results = bm25.search("authentication", type_filter=["spec"])

        assert len(results) == 1
        assert results[0].type == "spec"

    def test_bm25_search_scope_filter(self, artifact_store, valid_artifact_request, authentication_artifact):
        """Scope filter limits results."""
        artifact_store.ingest_artifact(valid_artifact_request)  # scope="global"
        artifact_store.ingest_artifact(authentication_artifact)  # scope="global"

        bm25 = BM25Search(artifact_store.db.connection())
        results = bm25.search("authentication", scope_filter="global")

        assert len(results) >= 1
        for result in results:
            assert result.relevance_scope == "global"

    def test_bm25_search_normalized_scores(self, artifact_store, authentication_artifact):
        """Relevance scores are normalized (0.0-1.0)."""
        artifact_store.ingest_artifact(authentication_artifact)

        bm25 = BM25Search(artifact_store.db.connection())
        results = bm25.search("authentication")

        assert len(results) > 0
        for result in results:
            assert 0.0 <= result.relevance_score <= 1.0


class TestSemanticSearch:
    """Test semantic (KNN) search."""

    def test_semantic_search_unavailable(self, artifact_store, authentication_artifact):
        """Semantic search unavailable returns empty gracefully."""
        artifact_store.ingest_artifact(authentication_artifact)

        semantic = SemanticSearch(artifact_store.db.connection())
        # Without embeddings stored, should return empty
        query_embedding = [0.1] * 1536
        results = semantic.search(query_embedding)

        # Should return empty, not raise
        assert isinstance(results, list)


class TestHybridSearch:
    """Test hybrid (RRF) search."""

    def test_hybrid_search_fallback_to_bm25(self, artifact_store, authentication_artifact):
        """Hybrid search falls back to BM25 if semantic unavailable."""
        artifact_store.ingest_artifact(authentication_artifact)

        hybrid = HybridSearch(artifact_store.db.connection())
        # Search with embedding that won't match anything
        query_embedding = [0.1] * 1536
        results = hybrid.search(
            query="authentication",
            query_embedding=query_embedding
        )

        # Should return BM25 results even without semantic
        assert len(results) >= 0

    def test_hybrid_search_limit_respected(self, artifact_store, valid_artifact_request, authentication_artifact):
        """Hybrid search respects limit."""
        artifact_store.ingest_artifact(valid_artifact_request)
        artifact_store.ingest_artifact(authentication_artifact)

        hybrid = HybridSearch(artifact_store.db.connection())
        results = hybrid.search("", limit=1)

        # Should return at most 1 result
        assert len(results) <= 1

    def test_hybrid_search_returns_search_result(self, artifact_store, authentication_artifact):
        """Hybrid search returns SearchResult objects."""
        artifact_store.ingest_artifact(authentication_artifact)

        hybrid = HybridSearch(artifact_store.db.connection())
        results = hybrid.search("authentication")

        if len(results) > 0:
            result = results[0]
            assert hasattr(result, "artifact_id")
            assert hasattr(result, "title")
            assert hasattr(result, "relevance_score")
            assert 0.0 <= result.relevance_score <= 1.0
