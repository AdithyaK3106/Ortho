"""Prompt assembler: Deterministic formatting per spec.md AC4."""

from typing import Any, Optional

from .types import ContextPackage


def assemble_prompt(
    context_package: ContextPackage,
    step: Any,  # ExecutionStep
    agent: Any,  # AgentManifest
    skills: Optional[list[Any]] = None,
    intent_text: str = "",
) -> tuple[str, str]:
    """Assemble system prompt and user message from context.

    System Prompt:
    - Concatenates agent.system_prompt + skill prompts (unchanged from step_runner logic)
    - Deterministic (no token_optimizer innovations)

    User Message:
    - Only chunks where included=True (respects budget decisions)
    - Chunks ordered by chunk.id ascending (lexicographic, deterministic)
    - Format: "\\n\\n--- [{source_type}:{source_id}] ---\\n{content}\\n" per chunk
    - Fixed delimiter, content verbatim, no escaping or truncation
    - When no chunks are included, falls back to "Original request: {intent_text}"
      rather than an empty string: a real ArtifactStore with nothing ingested
      yet for this repo returns a real (truthy) ContextPackage with zero
      chunks -- indistinguishable from "context assembly worked but found
      nothing" without this fallback, an agent received a genuinely empty
      user message and could only ask "what am I reviewing?"

    Determinism Guarantee:
    Identical input → identical prompt text (chunk order and format deterministic).

    Args:
        context_package: ContextPackage from assembler (contains chunks with included flag)
        step: ExecutionStep (unused; for future extensibility)
        agent: AgentManifest (has system_prompt)
        skills: list[SkillManifest] (each has content or system_prompt)
        intent_text: the user's original request text, used as a fallback
            when no context chunks were included

    Returns:
        (system_prompt: str, user_message: str) tuple
    """
    if skills is None:
        skills = []

    # System prompt: agent + skills (unchanged from step_runner._assemble_system_prompt)
    system_prompt = agent.system_prompt if hasattr(agent, 'system_prompt') else ""

    if skills:
        system_prompt += "\n\n## Available Skills\n\n"
        for skill in skills:
            system_prompt += f"### {skill.display_name}\n"
            # Real Skill manifests carry the .md body as system_prompt;
            # older test doubles used .content. Accept either.
            body = getattr(skill, "content", None) or getattr(skill, "system_prompt", "")
            system_prompt += f"{body}\n\n"

    # User message: included chunks only, ordered by chunk.id ascending
    included_chunks = [c for c in context_package.chunks if c.included]
    included_chunks.sort(key=lambda c: c.id)  # Deterministic order by chunk.id ascending

    user_message_parts = []
    for chunk in included_chunks:
        # Format: \n\n--- [{source_type}:{source_id}] ---\n{content}\n
        formatted = f"\n\n--- [{chunk.source_type}:{chunk.source_id}] ---\n{chunk.content}\n"
        user_message_parts.append(formatted)

    if user_message_parts:
        user_message = "".join(user_message_parts)
    elif intent_text:
        user_message = f"Original request: {intent_text}"
    else:
        user_message = ""

    return system_prompt, user_message
