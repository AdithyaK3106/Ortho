"""Context assembler: Greedy packing with deterministic tie-breaking per spec.md AC3."""

import uuid
from datetime import datetime
from .budget import TokenBudget
from .types import ContextChunk, ContextPackage


def assemble_context(
    query: str,
    repo_id: str,
    artifact_store,  # ArtifactStore
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
    # Search for candidate artifacts
    artifacts = artifact_store.search(query, repo_id=repo_id)

    # Convert each artifact to ContextChunk
    chunks = []
    for artifact in artifacts:
        chunk = ContextChunk(
            id=str(artifact.id),
            source_type="artifact",
            source_id=str(artifact.id),
            content=artifact.content if hasattr(artifact, 'content') else "",
            relevance_score=getattr(artifact, 'relevance_score', 0.0),
            token_count=artifact.estimated_tokens if hasattr(artifact, 'estimated_tokens') else 0,
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
