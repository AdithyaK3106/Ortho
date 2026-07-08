"""AgentRegistry: loads and caches agents from .md files."""

import logging
import yaml
from pathlib import Path
from typing import Optional

from .types import Agent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Loads and caches agents from .ases/agents/core/ and .ases/agents/custom/.
    Cache is immutable after initialization. No reload() method; create a new instance to refresh.
    If duplicate agent names exist in both core/ and custom/, custom/ entry wins.
    """

    def __init__(self, agents_root: Path = Path(".ases/agents")) -> None:
        """
        Load all agents from agents_root/core/*.md and agents_root/custom/*.md.
        Files are loaded in order: core/ first, then custom/ (custom overrides core on name collision).
        Malformed YAML or missing required fields cause the file to be skipped with a warning logged.

        Raises:
            FileNotFoundError: if agents_root/core/ does not exist.
        """
        self.agents_root = Path(agents_root)
        core_dir = self.agents_root / "core"

        if not core_dir.exists():
            raise FileNotFoundError(f"Agents core directory not found: {core_dir}")

        self._agents: dict[str, Agent] = {}

        # Load core agents
        for md_file in sorted(core_dir.glob("*.md")):
            self._load_agent_file(md_file)

        # Load custom agents (override core on name collision)
        custom_dir = self.agents_root / "custom"
        if custom_dir.exists():
            for md_file in sorted(custom_dir.glob("*.md")):
                self._load_agent_file(md_file)

    def _load_agent_file(self, md_file: Path) -> None:
        """Parse a single .md file and add agent to cache (or skip if invalid)."""
        try:
            content = md_file.read_text(encoding="utf-8")
            if not content.strip():
                logger.warning(f"Agent file is empty: {md_file}")
                return

            # Split frontmatter and body
            parts = content.split("---", 2)
            if len(parts) < 3:
                logger.warning(f"Agent file missing frontmatter delimiter: {md_file}")
                return

            frontmatter_str = parts[1]
            body = parts[2].strip()

            # Parse YAML frontmatter
            try:
                frontmatter = yaml.safe_load(frontmatter_str) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter in {md_file.name}: {e}")
                return

            # Validate required fields
            required_fields = [
                "name",
                "display_name",
                "description",
                "intent_triggers",
                "skills_preferred",
                "priority",
                "requires_context",
            ]
            for field in required_fields:
                if field not in frontmatter:
                    logger.warning(
                        f"Agent {md_file.name} missing required field: '{field}'"
                    )
                    return

            # Validate types
            if not isinstance(frontmatter.get("intent_triggers"), list):
                logger.warning(
                    f"Agent {md_file.name} intent_triggers must be a list"
                )
                return
            if not isinstance(frontmatter.get("skills_preferred"), list):
                logger.warning(
                    f"Agent {md_file.name} skills_preferred must be a list"
                )
                return
            if not isinstance(frontmatter.get("requires_context"), list):
                logger.warning(
                    f"Agent {md_file.name} requires_context must be a list"
                )
                return

            agent = Agent(
                name=frontmatter["name"],
                display_name=frontmatter["display_name"],
                description=frontmatter["description"],
                intent_triggers=frontmatter["intent_triggers"],
                skills_preferred=frontmatter["skills_preferred"],
                priority=frontmatter["priority"],
                requires_context=frontmatter["requires_context"],
                system_prompt=body,
            )

            self._agents[agent.name] = agent

        except Exception as e:
            logger.warning(f"Error loading agent from {md_file}: {e}")

    def list_agents(self) -> list[Agent]:
        """
        Return all successfully loaded agents sorted by name.
        Skipped entries (due to validation errors) are not included.
        """
        return sorted(self._agents.values(), key=lambda a: a.name)

    # SelectorEngine (task-013) calls all_agents(); keep both names as one method.
    all_agents = list_agents

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name from cache, or None if not found or skipped due to validation error."""
        return self._agents.get(name)

    def get_agents_by_intent(self, intent_type: str) -> list[Agent]:
        """Get all agents whose intent_triggers contain intent_type (substring match). Sorted by name."""
        intent_lower = intent_type.lower()
        matching = [
            agent
            for agent in self._agents.values()
            if any(intent_lower in trigger.lower() for trigger in agent.intent_triggers)
        ]
        return sorted(matching, key=lambda a: a.name)
