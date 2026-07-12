"""Architecture-aware chunk retrieval and weighting."""

from dataclasses import replace
from typing import List, Dict, Optional, Any

from .types import ContextChunk


def boost_by_architecture(
    chunks: List[ContextChunk],
    architecture_model: Optional[Any] = None,
    centrality_weights: Optional[Dict[str, Dict[str, float]]] = None,
) -> List[ContextChunk]:
    """
    Boost relevance scores for architecturally central chunks.

    Strategy:
    - If architecture_model is None, return chunks unchanged
    - For each chunk, look up source in architecture model
    - If in central layer (e.g., "service"), multiply by centrality_weight
    - If in low-coupling subsystem, multiply by subsystem boost
    - Apply max boost (not cumulative)
    - Re-sort by relevance_score descending, then chunk.id

    Args:
        chunks: Candidate chunks
        architecture_model: ArchitectureModel from arch-intelligence (or None)
        centrality_weights: Config per style (uses defaults if None)

    Returns:
        Same chunks, relevance_score boosted, resorted

    Raises:
        ValueError: If centrality_weights contains negative values
    """
    # Early exit if no architecture model
    if architecture_model is None:
        return chunks

    if not chunks:
        return chunks

    if centrality_weights is None:
        centrality_weights = _default_centrality_weights()
    else:
        # Validate weights (all must be positive)
        for style_weights in centrality_weights.values():
            for weight in style_weights.values():
                if weight < 0.0:
                    raise ValueError(
                        f"All centrality weights must be non-negative, got {weight}"
                    )

    # Get architecture style
    arch_style = getattr(architecture_model, "style", "unknown")
    style_weights = centrality_weights.get(arch_style, {})

    # Boost each chunk
    boosted_chunks = []
    for chunk in chunks:
        boost_factor = _compute_boost_factor(chunk, architecture_model, style_weights)
        new_score = chunk.relevance_score * boost_factor

        boosted_chunk = replace(chunk, relevance_score=new_score)
        boosted_chunks.append(boosted_chunk)

    # Re-sort by relevance_score descending, then chunk.id
    boosted_chunks.sort(key=lambda c: (-c.relevance_score, c.id))

    return boosted_chunks


def _default_centrality_weights() -> Dict[str, Dict[str, float]]:
    """Default centrality weights per architecture style."""
    return {
        "layered": {
            "service": 1.5,
            "domain": 1.4,
            "data": 1.3,
            "presentation": 1.0,
        },
        "microservices": {
            "low_coupling": 1.3,
            "high_coupling": 1.0,
        },
        "hexagonal": {
            "domain": 1.5,
            "adapter": 1.2,
            "port": 1.1,
        },
        "mvc": {
            "model": 1.5,
            "controller": 1.3,
            "view": 1.0,
        },
        "flat": {},  # No boost for flat architecture
    }


def _compute_boost_factor(
    chunk: ContextChunk,
    architecture_model: Any,
    style_weights: Dict[str, float],
) -> float:
    """
    Compute boost factor for a chunk based on architecture model.

    Checks:
    1. Chunk's source_id in any layer → apply layer weight
    2. Chunk's source_id in any subsystem → apply subsystem weight
    3. Returns max of layer boost and subsystem boost

    Args:
        chunk: ContextChunk to evaluate
        architecture_model: ArchitectureModel
        style_weights: Weights dict for this architecture style

    Returns:
        Boost factor (1.0 or higher)
    """
    if not style_weights:
        return 1.0

    max_boost = 1.0

    # Check layers (if architecture model has them)
    layers = getattr(architecture_model, "layers", [])
    for layer in layers:
        layer_name = getattr(layer, "name", "").lower()
        file_ids = getattr(layer, "file_ids", [])

        # Check if chunk's source is in this layer
        if chunk.source_id in file_ids and layer_name in style_weights:
            boost = style_weights[layer_name]
            max_boost = max(max_boost, boost)

    # Check subsystems (if architecture model has them)
    subsystems = getattr(architecture_model, "subsystems", [])
    for subsystem in subsystems:
        subsystem_name = getattr(subsystem, "name", "").lower()
        file_ids = getattr(subsystem, "file_ids", [])
        coupling_score = getattr(subsystem, "coupling_score", 0.5)

        # Map coupling to weight name
        if chunk.source_id in file_ids:
            if coupling_score < 0.5 and "low_coupling" in style_weights:
                boost = style_weights["low_coupling"]
                max_boost = max(max_boost, boost)
            elif coupling_score >= 0.5 and "high_coupling" in style_weights:
                boost = style_weights["high_coupling"]
                max_boost = max(max_boost, boost)

    return max_boost
