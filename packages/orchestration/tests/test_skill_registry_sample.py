"""Sample tests for SkillRegistry (task-012)."""

import pytest
from pathlib import Path
import tempfile
import logging
from orchestration.selector.skill_registry import SkillRegistry
from orchestration.selector.types import Skill


class TestSkillRegistryCoreLoad:
    """Test loading skills from core/ directory."""

    def test_skill_registry_loads_exactly_10_core_skills(self):
        """Verify all 10 core skills load without skipping."""
        reg = SkillRegistry(Path(".ases/skills"))
        skills = reg.list_skills()

        assert len(skills) == 10, f"Expected 10 skills, got {len(skills)}"
        skill_names = {s.name for s in skills}
        expected = {"repo-analysis", "adr-writer", "impact-analyzer", "test-generator",
                   "code-reviewer", "context-retriever", "git-analyst", "debt-analyzer",
                   "spec-writer", "debug-tracer"}
        assert skill_names == expected, f"Missing or extra skills: {skill_names ^ expected}"

    def test_skill_registry_get_skill_adr_writer_returns_populated(self):
        """Verify get_skill() returns Skill with all fields populated."""
        reg = SkillRegistry(Path(".ases/skills"))
        skill = reg.get_skill("adr-writer")

        assert skill is not None, "Expected skill 'adr-writer' to exist"
        assert skill.name == "adr-writer"
        assert skill.display_name is not None
        assert len(skill.intent_triggers) > 0
        assert len(skill.provides) > 0
        assert skill.estimated_tokens > 0
        assert skill.system_prompt is not None

    def test_skill_registry_list_skills_sorted_by_name(self):
        """Verify list_skills() returns skills sorted by name."""
        reg = SkillRegistry(Path(".ases/skills"))
        skills = reg.list_skills()

        names = [s.name for s in skills]
        assert names == sorted(names), "Skills should be sorted by name"


class TestSkillRegistryCaching:
    """Test cache behavior."""

    def test_skill_registry_cache_reused_on_multiple_calls(self):
        """Verify list_skills() returns same cached object."""
        reg = SkillRegistry(Path(".ases/skills"))
        list1 = reg.list_skills()
        list2 = reg.list_skills()

        assert id(list1) == id(list2) or list1 == list2

    def test_skill_registry_no_reload_method_exists(self):
        """Verify no reload() method exists (immutable cache)."""
        reg = SkillRegistry(Path(".ases/skills"))
        assert not hasattr(reg, 'reload'), "SkillRegistry should not have reload() method"


class TestSkillRegistryLookup:
    """Test query methods."""

    def test_skill_registry_get_skill_not_found_returns_none(self):
        """Verify get_skill() returns None for nonexistent skill."""
        reg = SkillRegistry(Path(".ases/skills"))
        skill = reg.get_skill("nonexistent-skill")
        assert skill is None

    def test_skill_registry_get_skills_for_agent(self):
        """Verify get_skills_for_agent() filters correctly."""
        reg = SkillRegistry(Path(".ases/skills"))
        architect_skills = reg.get_skills_for_agent("architect")

        # At least adr-writer should be for architect
        assert any(s.name == "adr-writer" for s in architect_skills)
        # Verify only skills with "architect" in agent_types are returned
        for skill in architect_skills:
            assert "architect" in skill.agent_types


class TestSkillRegistryDuplicates:
    """Test duplicate name policy (custom > core)."""

    def test_skill_registry_custom_overrides_core_on_duplicate_name(self):
        """Verify custom skill overrides core skill with same name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create core/ and custom/ directories
            core_dir = tmppath / "core"
            custom_dir = tmppath / "custom"
            core_dir.mkdir()
            custom_dir.mkdir()

            # Create core skill
            core_skill = core_dir / "duplicate-skill.md"
            core_skill.write_text("""---
name: duplicate-skill
display_name: Core Skill
description: Core version
agent_types:
  - architect
intent_triggers:
  - core trigger
provides:
  - core_output
estimated_tokens: 1000
---
Core system prompt.
""")

            # Create custom skill with same name
            custom_skill = custom_dir / "duplicate-skill.md"
            custom_skill.write_text("""---
name: duplicate-skill
display_name: Custom Skill
description: Custom version
agent_types:
  - coder
intent_triggers:
  - custom trigger
provides:
  - custom_output
estimated_tokens: 2000
---
Custom system prompt.
""")

            # Load registry
            reg = SkillRegistry(tmppath)
            skill = reg.get_skill("duplicate-skill")

            # Verify custom version wins
            assert skill.display_name == "Custom Skill"
            assert skill.estimated_tokens == 2000
            assert "custom trigger" in skill.intent_triggers


class TestSkillRegistryValidation:
    """Test frontmatter validation (skip on error)."""

    def test_skill_registry_malformed_yaml_skipped_with_warning(self, caplog):
        """Verify malformed YAML is skipped with warning logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            core_dir = tmppath / "core"
            core_dir.mkdir()
            custom_dir = tmppath / "custom"
            custom_dir.mkdir()

            # Create malformed skill
            bad_skill = core_dir / "bad-skill.md"
            bad_skill.write_text("""---
name: bad-skill
display_name Bad Skill Name
estimated_tokens: 1000
---
""")

            # Load registry with logging capture
            with caplog.at_level(logging.WARNING):
                reg = SkillRegistry(tmppath)

            # Verify skill is not in cache
            skill = reg.get_skill("bad-skill")
            assert skill is None, "Malformed skill should not be loaded"

    def test_skill_registry_invalid_estimated_tokens_type_skipped(self, caplog):
        """Verify invalid data type for estimated_tokens causes skip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            core_dir = tmppath / "core"
            core_dir.mkdir()
            custom_dir = tmppath / "custom"
            custom_dir.mkdir()

            # Create skill with invalid estimated_tokens type
            bad_skill = core_dir / "bad-token-skill.md"
            bad_skill.write_text("""---
name: bad-token-skill
display_name: Bad Token Skill
description: Invalid token type
agent_types:
  - architect
intent_triggers:
  - test
provides:
  - output
estimated_tokens: "2000"
---
""")

            with caplog.at_level(logging.WARNING):
                reg = SkillRegistry(tmppath)

            skill = reg.get_skill("bad-token-skill")
            assert skill is None, "Skill with invalid estimated_tokens type should not be loaded"


class TestSkillRegistryEdgeCases:
    """Test edge cases."""

    def test_skill_registry_with_unicode_in_system_prompt(self):
        """Verify unicode characters in skill prompt don't break parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            core_dir = tmppath / "core"
            core_dir.mkdir()
            custom_dir = tmppath / "custom"
            custom_dir.mkdir()

            # Create skill with unicode
            unicode_skill = core_dir / "unicode-skill.md"
            unicode_skill.write_text("""---
name: unicode-skill
display_name: Unicode Skill
description: Handles émoji and café
agent_types:
  - architect
intent_triggers:
  - test
provides:
  - output
estimated_tokens: 1000
---
You are expert in: ñ, é, 中文, 日本語, emoji 🎯
""", encoding="utf-8")

            reg = SkillRegistry(tmppath)
            skill = reg.get_skill("unicode-skill")

            assert skill is not None
            assert "émoji" in skill.description
            assert "🎯" in skill.system_prompt

    def test_skill_registry_core_dir_missing_raises_filenotfounderror(self):
        """Verify FileNotFoundError raised if core/ directory missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Don't create core/ directory

            with pytest.raises(FileNotFoundError):
                SkillRegistry(tmppath)
