"""Per-model prompt adaptation and formatting."""

from typing import Tuple


def adapt_prompt_for_model(
    system_prompt: str,
    user_message: str,
    model: str,
) -> Tuple[str, str]:
    """
    Adapt prompt format and content for specific model.

    Applies model-specific transformations:
    - claude-opus-4-8: Identity (no change)
    - claude-haiku-4-5-*: Remove verbose sections, prioritize essentials
    - gpt-4*: Adjust format (different token counting), add conciseness hint
    - gpt-4o: GPT-4 adjustments + JSON output hint
    - Unknown: Identity (fallback)

    Args:
        system_prompt: Original system prompt
        user_message: Original user message
        model: Model identifier (e.g., 'claude-opus-4-8')

    Returns:
        (adapted_system_prompt, adapted_user_message)
    """
    model_lower = model.lower()

    # Route to appropriate adapter
    if "opus-4-8" in model_lower or "opus-4-7" in model_lower:
        return system_prompt, user_message

    elif "haiku-4-5" in model_lower:
        return _adapt_haiku(system_prompt, user_message)

    elif "gpt-4o" in model_lower:
        return _adapt_gpt4o(system_prompt, user_message)

    elif "gpt-4" in model_lower:
        return _adapt_gpt4(system_prompt, user_message)

    else:
        # Unknown model: identity fallback
        return system_prompt, user_message


def _adapt_haiku(system_prompt: str, user_message: str) -> Tuple[str, str]:
    """
    Adapt for Claude Haiku (smaller context, needs conciseness).

    Strategy:
    - Keep only first 2 paragraphs of system prompt
    - Remove verbose explanations (>200 words per section)
    - Keep user message unchanged
    """
    if not system_prompt:
        return system_prompt, user_message

    # ponytail: split by double newline (paragraph boundary)
    paragraphs = system_prompt.split("\n\n")

    # Keep first 2 paragraphs max
    kept = paragraphs[:2]
    adapted_system = "\n\n".join(kept)

    # Trim if still too verbose (>500 chars for haiku)
    if len(adapted_system) > 500:
        # Find last sentence in first ~400 chars
        text = adapted_system[:400]
        last_period = text.rfind(".")
        if last_period > 0:
            adapted_system = text[: last_period + 1]
        else:
            adapted_system = text

    return adapted_system, user_message


def _adapt_gpt4(system_prompt: str, user_message: str) -> Tuple[str, str]:
    """
    Adapt for GPT-4 (different token counting).

    Strategy:
    - Add conciseness reminder
    - No verbose explanations (GPT counts tokens differently)
    """
    # Add conciseness hint if not already present
    conciseness_hint = "Be concise and direct in your response."
    if conciseness_hint not in system_prompt:
        system_prompt = f"{system_prompt}\n\n{conciseness_hint}"

    return system_prompt, user_message


def _adapt_gpt4o(system_prompt: str, user_message: str) -> Tuple[str, str]:
    """
    Adapt for GPT-4o (vision + text, prefers JSON).

    Strategy:
    - GPT-4 adaptations
    - Add JSON output hint if applicable
    """
    # Apply GPT-4 adaptations first
    system_prompt, user_message = _adapt_gpt4(system_prompt, user_message)

    # Add JSON hint if not present
    json_hint = "Use JSON output format when applicable."
    if json_hint not in system_prompt and "json" not in user_message.lower():
        system_prompt = f"{system_prompt}\n\n{json_hint}"

    return system_prompt, user_message
