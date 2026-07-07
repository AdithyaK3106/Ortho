"""Intent routing types."""

from dataclasses import dataclass


@dataclass
class IntentClassification:
    """
    Result of classifying a user intent.

    type: The agent type selected (e.g., "architect", "coder", "reviewer", "orchestrator").
    confidence: Raw semantic similarity score [0.0, 1.0] from semantic-router (not a calibrated probability).
               Exposed directly; threshold (0.7) is internal to IntentRouter.classify_intent().
    method: "router" (semantic-router fast path, confidence >= 0.7) or "llm_fallback" (confidence < 0.7, needs LLM).
    """

    type: str  # agent type (e.g., "architect", "coder", "llm_fallback")
    confidence: float  # [0.0, 1.0], raw semantic similarity score
    method: str  # "router" or "llm_fallback"
