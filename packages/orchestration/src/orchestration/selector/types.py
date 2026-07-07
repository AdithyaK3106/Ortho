"""Selector types: Agent and Skill dataclasses parsed from .md frontmatter."""

from dataclasses import dataclass


@dataclass
class Agent:
    """Parsed agent metadata from .md frontmatter."""

    name: str
    display_name: str
    description: str
    intent_triggers: list[str]
    skills_preferred: list[str]
    priority: str  # "high", "medium", "low"
    requires_context: list[str]
    system_prompt: str  # body of .md file (after frontmatter)


@dataclass
class Skill:
    """Parsed skill metadata from .md frontmatter."""

    name: str
    display_name: str
    description: str
    agent_types: list[str]
    intent_triggers: list[str]
    provides: list[str]
    estimated_tokens: int
    system_prompt: str  # body of .md file
