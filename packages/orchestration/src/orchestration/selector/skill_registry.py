"""SkillRegistry: loads and caches skills from .md files."""

import logging
import yaml
from pathlib import Path
from typing import Optional

from .types import Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Loads and caches skills from .ases/skills/core/ and .ases/skills/custom/.
    Cache is immutable after initialization. No reload() method; create a new instance to refresh.
    If duplicate skill names exist in both core/ and custom/, custom/ entry wins.
    """

    def __init__(self, skills_root: Path = Path(".ases/skills")) -> None:
        """
        Load all skills from skills_root/core/*.md and skills_root/custom/*.md.
        Files are loaded in order: core/ first, then custom/ (custom overrides core on name collision).
        Malformed YAML or missing required fields cause the file to be skipped with a warning logged.

        Raises:
            FileNotFoundError: if skills_root/core/ does not exist.
        """
        self.skills_root = Path(skills_root)
        core_dir = self.skills_root / "core"

        if not core_dir.exists():
            raise FileNotFoundError(f"Skills core directory not found: {core_dir}")

        self._skills: dict[str, Skill] = {}

        # Load core skills
        for md_file in sorted(core_dir.glob("*.md")):
            self._load_skill_file(md_file)

        # Load custom skills (override core on name collision)
        custom_dir = self.skills_root / "custom"
        if custom_dir.exists():
            for md_file in sorted(custom_dir.glob("*.md")):
                self._load_skill_file(md_file)

    def _load_skill_file(self, md_file: Path) -> None:
        """Parse a single .md file and add skill to cache (or skip if invalid)."""
        try:
            content = md_file.read_text(encoding="utf-8")
            if not content.strip():
                logger.warning(f"Skill file is empty: {md_file}")
                return

            # Split frontmatter and body
            parts = content.split("---", 2)
            if len(parts) < 3:
                logger.warning(f"Skill file missing frontmatter delimiter: {md_file}")
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
                "agent_types",
                "intent_triggers",
                "provides",
                "estimated_tokens",
            ]
            for field in required_fields:
                if field not in frontmatter:
                    logger.warning(
                        f"Skill {md_file.name} missing required field: '{field}'"
                    )
                    return

            # Validate types
            if not isinstance(frontmatter.get("agent_types"), list):
                logger.warning(f"Skill {md_file.name} agent_types must be a list")
                return
            if not isinstance(frontmatter.get("intent_triggers"), list):
                logger.warning(f"Skill {md_file.name} intent_triggers must be a list")
                return
            if not isinstance(frontmatter.get("provides"), list):
                logger.warning(f"Skill {md_file.name} provides must be a list")
                return
            if not isinstance(frontmatter.get("estimated_tokens"), int):
                logger.warning(
                    f"Skill {md_file.name} estimated_tokens must be an integer"
                )
                return

            skill = Skill(
                name=frontmatter["name"],
                display_name=frontmatter["display_name"],
                description=frontmatter["description"],
                agent_types=frontmatter["agent_types"],
                intent_triggers=frontmatter["intent_triggers"],
                provides=frontmatter["provides"],
                estimated_tokens=frontmatter["estimated_tokens"],
                system_prompt=body,
            )

            self._skills[skill.name] = skill

        except Exception as e:
            logger.warning(f"Error loading skill from {md_file}: {e}")

    def list_skills(self) -> list[Skill]:
        """
        Return all successfully loaded skills sorted by name.
        Skipped entries (due to validation errors) are not included.
        """
        return sorted(self._skills.values(), key=lambda s: s.name)

    # SelectorEngine (task-013) calls all_skills(); keep both names as one method.
    all_skills = list_skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get skill by name from cache, or None if not found or skipped due to validation error."""
        return self._skills.get(name)

    def get_skills_for_agent(self, agent_name: str) -> list[Skill]:
        """Get skills whose agent_types list contains agent_name. Sorted by name."""
        matching = [
            skill
            for skill in self._skills.values()
            if agent_name in skill.agent_types
        ]
        return sorted(matching, key=lambda s: s.name)
