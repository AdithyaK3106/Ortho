"""ContextChunk and ContextPackage types per spec.md AC2."""

from dataclasses import dataclass
from typing import List


@dataclass
class ContextChunk:
    """A chunk of context (symbol, artifact, git history, or architecture data).

    Fields match spec.md AC2 and FRD §5 ContextChunk interface.
    """
    id: str                    # Unique chunk ID (e.g., artifact UUID)
    source_type: str          # "symbol" | "artifact" | "git" | "architecture"
    source_id: str            # ID of source (e.g., artifact.id, symbol name)
    content: str              # Chunk content (verbatim)
    relevance_score: float    # Relevance score (0.0-1.0) for sorting
    token_count: int          # Pre-computed token count
    included: bool            # True if included in context package (budget-aware)


@dataclass
class ContextPackage:
    """Assembled context chunks for a workflow step.

    Fields match spec.md AC2 and FRD §5 ContextPackage interface.
    ContextPackage is immutable after assembly (chunk list and budget state are final).
    """
    id: str                    # Unique package ID (UUID)
    workflow_run_id: str      # Workflow run ID (for traceability)
    step_id: str              # Orchestration step ID (for traceability)
    chunks: List[ContextChunk]  # All chunks (both included and excluded)
    budget: 'TokenBudget'     # Token budget (same instance passed in, modified in place)
    assembled_at: str         # ISO datetime when package was assembled
