"""IntentRouter: semantic routing with semantic-router library."""

import logging
from typing import Optional

from semantic_router import Route, SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

from .types import IntentClassification
from .classifier import llm_classify_intent

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7


class IntentRouter:
    """
    Routes user utterances to agents using semantic-router (HuggingFace encoder, BAAI/bge-small-en-v1.5).
    Immutable after initialization. Threshold is hardcoded to 0.7 for this task.

    Confidence field is the raw semantic similarity score [0.0, 1.0] from semantic-router.
    It is NOT a calibrated probability, only a similarity metric.
    """

    def __init__(self, utterances_corpus: dict[str, list[str]]) -> None:
        """
        Build routes from utterance corpus.

        utterances_corpus: {agent_type: [utterance1, utterance2, ...], ...}
        Internally creates semantic_router.SemanticRouter with HuggingFaceEncoder("BAAI/bge-small-en-v1.5").

        Raises:
            RuntimeError: if HuggingFace encoder fails to load.
        """
        try:
            encoder = HuggingFaceEncoder(model="BAAI/bge-small-en-v1.5")
        except Exception as e:
            raise RuntimeError(f"Failed to load HuggingFace encoder: {e}") from e

        # Build routes from utterance corpus
        routes = [
            Route(name=agent_type, utterances=utterances)
            for agent_type, utterances in utterances_corpus.items()
        ]

        self.router = SemanticRouter(encoder=encoder, routes=routes)

    def classify_intent(self, user_input: str) -> IntentClassification:
        """
        Classify user input against routes using semantic similarity.

        Returns IntentClassification with:
        - type: The agent type (route.name) or "orchestrator" (fallback)
        - confidence: Raw similarity score [0.0, 1.0] from semantic-router
        - method: "router" if confidence >= 0.7, else "llm_fallback"

        Routing logic:
        - If best route has similarity_score >= 0.7 and route.name is not None:
          return IntentClassification(type=route.name, confidence=score, method="router")
        - Otherwise:
          return IntentClassification(..., method="llm_fallback") and call llm_classify_intent()

        Note: llm_classify_intent() is a stub; no live LLM yet (documented limitation).
        """
        try:
            result = self.router.classify(user_input)

            # Extract route name and score
            route_name: Optional[str] = result.route.name if result.route else None
            score: float = result.score if hasattr(result, "score") else 0.0

            # Apply threshold
            if score >= CONFIDENCE_THRESHOLD and route_name:
                return IntentClassification(
                    type=route_name, confidence=score, method="router"
                )
            else:
                # Fallback to LLM classifier
                fallback_result = llm_classify_intent(user_input)
                return fallback_result

        except Exception as e:
            logger.warning(f"Intent router error, falling back to LLM: {e}")
            return llm_classify_intent(user_input)
