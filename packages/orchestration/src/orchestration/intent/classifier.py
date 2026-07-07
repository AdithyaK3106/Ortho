"""LLM fallback classifier stub."""

from .types import IntentClassification


def llm_classify_intent(
    user_input: str, fallback_context: str = ""
) -> IntentClassification:
    """
    Fallback classifier for when router confidence < 0.7.

    STUB: Returns IntentClassification(type="orchestrator", confidence=0.5, method="llm_fallback").
    Documented limitation: no live LLM call wired yet (task done when integrated in task-013 or later).

    Args:
        user_input: The user's input text to classify.
        fallback_context: Optional context for the classification (not used in stub).

    Returns:
        IntentClassification with fallback result.
    """
    return IntentClassification(
        type="orchestrator", confidence=0.5, method="llm_fallback"
    )
