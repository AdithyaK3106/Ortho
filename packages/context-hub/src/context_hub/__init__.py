"""ContextHub: Pillar 2 — Persistent knowledge layer."""

from .commit_evidence import CommitEvidence, find_relevant_commits
from .embedding import EmbeddingProvider, NullEmbedding
from .git_metadata import FileChurnMetadata, GitMetadataStore
from .ingestion import ArtifactIngestionRequest, ValidationResult, validate_ingestion
from .project_memory import ProjectMemory
from .search import BM25Search, HybridSearch, SearchResult, SemanticSearch
from .staleness import StalenessDetector, StalenessReport
from .store import Artifact, ArtifactStore

__all__ = [
    "ArtifactStore",
    "Artifact",
    "ArtifactIngestionRequest",
    "ValidationResult",
    "validate_ingestion",
    "SearchResult",
    "BM25Search",
    "SemanticSearch",
    "HybridSearch",
    "GitMetadataStore",
    "FileChurnMetadata",
    "ProjectMemory",
    "StalenessDetector",
    "StalenessReport",
    "EmbeddingProvider",
    "NullEmbedding",
    "CommitEvidence",
    "find_relevant_commits",
]
