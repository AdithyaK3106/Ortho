"""IntentRouter: semantic routing with semantic-router library."""

import logging
from typing import Optional

from semantic_router import Route
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router.routers import SemanticRouter

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
            # semantic-router 0.1.x: encoder model is the `name` field
            encoder = HuggingFaceEncoder(name="BAAI/bge-small-en-v1.5")
        except Exception as e:
            raise RuntimeError(f"Failed to load HuggingFace encoder: {e}") from e

        # Build routes from utterance corpus (sorted for determinism)
        routes = [
            Route(name=intent_type, utterances=utterances_corpus[intent_type])
            for intent_type in sorted(utterances_corpus)
        ]

        # auto_sync="local" builds the in-memory index immediately.
        # aggregation="max": confidence is the best single-utterance
        # similarity, matching this class's documented contract ("raw
        # semantic similarity score"); the default "mean" dilutes exact
        # matches below the 0.7 threshold when a route's other utterances
        # are dissimilar.
        self.router = SemanticRouter(
            encoder=encoder, routes=routes, auto_sync="local", aggregation="max"
        )

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
            # semantic-router 0.1.x: calling the router returns a RouteChoice
            result = self.router(user_input)

            route_name: Optional[str] = getattr(result, "name", None)
            score = getattr(result, "similarity_score", None)
            score = float(score) if score is not None else 0.0

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
