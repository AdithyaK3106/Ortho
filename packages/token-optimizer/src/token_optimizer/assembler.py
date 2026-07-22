"""Context assembler: Greedy packing with deterministic tie-breaking per spec.md AC3."""

import uuid
from datetime import datetime
from typing import Any

from .budget import TokenBudget
from .types import ContextChunk, ContextPackage


def assemble_context(
    query: str,
    repo_id: str,
    artifact_store: Any,  # ArtifactStore
    budget: TokenBudget,
    step_id: str,
    workflow_run_id: str,
    model: str = "claude",
) -> ContextPackage:
    """Assemble context chunks using greedy packing with deterministic tie-breaking.

    Behavior:
    - Searches for artifacts matching query
    - Converts each Artifact to ContextChunk
    - Sorts chunks deterministically: relevance_score desc → token_count asc → artifact.id asc
    - Greedily includes chunks while budget allows (modifies budget in place)
    - Returns ContextPackage with all chunks (included and excluded)

    Determinism Guarantee:
    Identical inputs (same query, repo_id, artifact_store state, budget.total/used) produce
    identical ContextPackage (same chunks, same included/excluded status, same token usage).

    Args:
        query: Search query for artifacts (e.g., "auth middleware")
        repo_id: Repository ID for filtering
        artifact_store: ArtifactStore interface (immutable; read-only)
        budget: TokenBudget (mutable; will be modified in place by consume() calls)
        step_id: Orchestration step ID (for traceability)
        workflow_run_id: Workflow run ID (for traceability)
        model: LLM model name (stored in budget, default "claude")

    Returns:
        ContextPackage with all candidate chunks (included and excluded), final budget state

    Side Effects:
        - Increments budget.used for each included chunk
        - No other mutations
    """
    # Search for candidate artifacts. ArtifactStore's repo scope is bound at
    # construction (ArtifactStore(db, repo_id)), not passed per-call --
    # search()'s real signature is (query, artifact_type=None, limit=50).
    # This call site was unreachable before wiring artifact_store into
    # WorkflowStateStore (hasattr() gated it to always skip), so the
    # mismatch never actually executed in production until now.
    artifacts = artifact_store.search(query)

    # Convert each real SearchResult to a ContextChunk. SearchResult (see
    # context_hub/search/result.py) has no "id" field -- its identity field
    # is "artifact_id" -- and no token estimate; this conversion previously
    # read .id/.estimated_tokens, attributes that don't exist on the real
    # object ArtifactStore.search() returns, and crashed with
    # "'SearchResult' object has no attribute 'id'" the moment a real
    # artifact_store (rather than the always-empty one before this
    # session's wiring) returned any real result.
    chunks = []
    for artifact in artifacts:
        content = artifact.content if hasattr(artifact, "content") else ""
        # SearchResult has no token estimate; a conservative chars/4
        # estimate (the same heuristic StubLLMClient uses for its own
        # token counts) keeps budget accounting meaningful for a real
        # search result. estimated_tokens is honored when present (test
        # doubles set it explicitly for deterministic tie-breaking
        # fixtures) so this stays backward compatible with those tests.
        token_count = getattr(artifact, "estimated_tokens", None)
        if token_count is None:
            token_count = len(content) // 4
        chunk = ContextChunk(
            id=str(artifact.artifact_id),
            source_type="artifact",
            source_id=str(artifact.artifact_id),
            content=content,
            relevance_score=getattr(artifact, "relevance_score", 0.0),
            token_count=token_count,
            included=False,  # Will be set to True if included in budget
        )
        chunks.append(chunk)

    # Sort deterministically: relevance_score desc → token_count asc → artifact.id asc
    # Use tuple key: (-relevance_score, token_count, source_id) for ascending token_count and ID
    chunks.sort(
        key=lambda c: (-c.relevance_score, c.token_count, c.source_id)
    )

    # Greedy inclusion: iterate sorted chunks, include while budget allows
    for chunk in chunks:
        if budget.can_fit(chunk.token_count):
            budget.consume(chunk.token_count)
            chunk.included = True

    # Return ContextPackage with all chunks and final budget state
    return ContextPackage(
        id=str(uuid.uuid4()),
        workflow_run_id=workflow_run_id,
        step_id=step_id,
        chunks=chunks,
        budget=budget,  # Same instance passed in, modified in place
        assembled_at=datetime.utcnow().isoformat(),
    )
