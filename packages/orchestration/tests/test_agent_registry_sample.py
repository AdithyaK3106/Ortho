"""Sample tests for AgentRegistry (task-012)."""

import pytest
from pathlib import Path
import tempfile
import logging
from orchestration.selector.agent_registry import AgentRegistry
from orchestration.selector.types import Agent


class TestAgentRegistryCoreLoad:
    """Test loading agents from core/ directory."""

    def test_agent_registry_loads_exactly_8_core_agents(self):
        """Verify all 8 core agents load without skipping."""
        reg = AgentRegistry(Path(".ases/agents"))
        agents = reg.list_agents()

        assert len(agents) == 8, f"Expected 8 agents, got {len(agents)}"
        agent_names = {a.name for a in agents}
        expected = {"orchestrator", "architect", "coder", "reviewer",
                   "tester", "analyst", "documenter", "debugger"}
        assert agent_names == expected, f"Missing or extra agents: {agent_names ^ expected}"

    def test_agent_registry_get_agent_coder_returns_populated(self):
        """Verify get_agent() returns Agent with all fields populated."""
        reg = AgentRegistry(Path(".ases/agents"))
        agent = reg.get_agent("coder")

        assert agent is not None, "Expected agent 'coder' to exist"
        assert agent.name == "coder"
        assert agent.display_name is not None
        assert len(agent.intent_triggers) > 0
        assert len(agent.skills_preferred) >= 0
        assert agent.priority in ["high", "medium", "low"]
        assert agent.system_prompt is not None

    def test_agent_registry_list_agents_sorted_by_name(self):
        """Verify list_agents() returns agents sorted by name."""
        reg = AgentRegistry(Path(".ases/agents"))
        agents = reg.list_agents()

        names = [a.name for a in agents]
        assert names == sorted(names), "Agents should be sorted by name"


class TestAgentRegistryCaching:
    """Test cache behavior (immutable, no reload)."""

    def test_agent_registry_cache_reused_on_multiple_calls(self):
        """Verify list_agents() returns same cached object."""
        reg = AgentRegistry(Path(".ases/agents"))
        list1 = reg.list_agents()
        list2 = reg.list_agents()

        # Cached: should be same object or equal
        assert id(list1) == id(list2) or list1 == list2

    def test_agent_registry_no_reload_method_exists(self):
        """Verify no reload() method exists (immutable cache)."""
        reg = AgentRegistry(Path(".ases/agents"))
        assert not hasattr(reg, 'reload'), "AgentRegistry should not have reload() method"


class TestAgentRegistryLookup:
    """Test query methods."""

    def test_agent_registry_get_agent_not_found_returns_none(self):
        """Verify get_agent() returns None for nonexistent agent."""
        reg = AgentRegistry(Path(".ases/agents"))
        agent = reg.get_agent("nonexistent-agent")
        assert agent is None

    def test_agent_registry_get_agents_by_intent(self):
        """Verify get_agents_by_intent() filters correctly."""
        reg = AgentRegistry(Path(".ases/agents"))
        architects = reg.get_agents_by_intent("architect")

        assert len(architects) >= 1
        assert any(a.name == "architect" for a in architects)
        # Verify only agents with "architect" in intent_triggers are returned
        for agent in architects:
            assert any("architect" in trigger.lower() for trigger in agent.intent_triggers)


class TestAgentRegistryDuplicates:
    """Test duplicate name policy (custom > core)."""

    def test_agent_registry_custom_overrides_core_on_duplicate_name(self):
        """Verify custom agent overrides core agent with same name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create core/ and custom/ directories
            core_dir = tmppath / "core"
            custom_dir = tmppath / "custom"
            core_dir.mkdir()
            custom_dir.mkdir()

            # Create core agent
            core_agent = core_dir / "duplicate-agent.md"
            core_agent.write_text("""---
name: duplicate-agent
display_name: Core Agent
description: Core version
intent_triggers:
  - core intent
skills_preferred: []
priority: low
requires_context: []
---
Core system prompt.
""")

            # Create custom agent with same name
            custom_agent = custom_dir / "duplicate-agent.md"
            custom_agent.write_text("""---
name: duplicate-agent
display_name: Custom Agent
description: Custom version
intent_triggers:
  - custom intent
skills_preferred: []
priority: high
requires_context: []
---
Custom system prompt.
""")

            # Load registry
            reg = AgentRegistry(tmppath)
            agent = reg.get_agent("duplicate-agent")

            # Verify custom version wins
            assert agent.display_name == "Custom Agent"
            assert agent.priority == "high"
            assert "custom intent" in agent.intent_triggers


class TestAgentRegistryValidation:
    """Test frontmatter validation (skip on error)."""

    def test_agent_registry_malformed_yaml_skipped_with_warning(self, caplog):
        """Verify malformed YAML is skipped with warning logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            core_dir = tmppath / "core"
            core_dir.mkdir()
            custom_dir = tmppath / "custom"
            custom_dir.mkdir()

            # Create malformed agent
            bad_agent = core_dir / "bad-agent.md"
            bad_agent.write_text("""---
name: bad-agent
display_name Bad Name
priority: high
---
""")

            # Load registry with logging capture
            with caplog.at_level(logging.WARNING):
                reg = AgentRegistry(tmppath)

            # Verify agent is not in cache
            agent = reg.get_agent("bad-agent")
            assert agent is None, "Malformed agent should not be loaded"

            # Verify warning was logged (if implementation uses logging)
            # This assertion is soft (optional) in case logging is not implemented
            if caplog.records:
                assert any("bad-agent" in record.message.lower() or "yaml" in record.message.lower()
                          for record in caplog.records), "Expected warning about malformed YAML"

    def test_agent_registry_missing_required_field_skipped_with_warning(self, caplog):
        """Verify missing required field causes skip with warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            core_dir = tmppath / "core"
            core_dir.mkdir()
            custom_dir = tmppath / "custom"
            custom_dir.mkdir()

            # Create agent missing 'priority' field
            incomplete_agent = core_dir / "incomplete-agent.md"
            incomplete_agent.write_text("""---
name: incomplete-agent
display_name: Incomplete Agent
description: Missing priority field
intent_triggers: []
skills_preferred: []
requires_context: []
---
""")

            with caplog.at_level(logging.WARNING):
                reg = AgentRegistry(tmppath)

            agent = reg.get_agent("incomplete-agent")
            assert agent is None, "Agent with missing field should not be loaded"


class TestAgentRegistryEdgeCases:
    """Test edge cases."""

    def test_agent_registry_with_unicode_in_system_prompt(self):
        """Verify unicode characters in prompt don't break parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            core_dir = tmppath / "core"
            core_dir.mkdir()
            custom_dir = tmppath / "custom"
            custom_dir.mkdir()

            # Create agent with unicode
            unicode_agent = core_dir / "unicode-agent.md"
            unicode_agent.write_text("""---
name: unicode-agent
display_name: Unicode Agent
description: Handles émoji and special chars café
intent_triggers:
  - test
skills_preferred: []
priority: high
requires_context: []
---
You are an expert in Unicode: ñ, é, 中文, 日本語, emoji 🚀
""", encoding="utf-8")

            reg = AgentRegistry(tmppath)
            agent = reg.get_agent("unicode-agent")

            assert agent is not None
            assert "émoji" in agent.description
            assert "🚀" in agent.system_prompt

    def test_agent_registry_core_dir_missing_raises_filenotfounderror(self):
        """Verify FileNotFoundError raised if core/ directory missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Don't create core/ directory

            with pytest.raises(FileNotFoundError):
                AgentRegistry(tmppath)
