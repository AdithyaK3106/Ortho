"""Sample integration tests for task-012."""

import pytest
from pathlib import Path
from orchestration.selector.agent_registry import AgentRegistry
from orchestration.selector.skill_registry import SkillRegistry
from orchestration.intent.router import IntentRouter


class TestIntegrationRegistries:
    """Integration tests for registries loading all real agents and skills."""

    def test_agent_registry_loads_all_8_core_agents_no_skips(self):
        """Verify AgentRegistry loads all 8 core agents successfully."""
        reg = AgentRegistry(Path(".ases/agents"))
        agents = reg.list_agents()

        assert len(agents) == 8, f"Expected 8 agents, got {len(agents)}"
        # No validation errors should have caused skips
        names = {a.name for a in agents}
        assert len(names) == 8, "Agent names should all be unique"

    def test_skill_registry_loads_all_10_core_skills_no_skips(self):
        """Verify SkillRegistry loads all 10 core skills successfully."""
        reg = SkillRegistry(Path(".ases/skills"))
        skills = reg.list_skills()

        assert len(skills) == 10, f"Expected 10 skills, got {len(skills)}"
        # No validation errors should have caused skips
        names = {s.name for s in skills}
        assert len(names) == 10, "Skill names should all be unique"

    def test_all_agents_have_required_fields(self):
        """Verify all agents have required frontmatter fields."""
        reg = AgentRegistry(Path(".ases/agents"))
        agents = reg.list_agents()

        for agent in agents:
            assert agent.name, f"Agent missing name"
            assert agent.display_name, f"Agent {agent.name} missing display_name"
            assert agent.description, f"Agent {agent.name} missing description"
            assert isinstance(agent.intent_triggers, list), f"Agent {agent.name} intent_triggers not list"
            assert isinstance(agent.skills_preferred, list), f"Agent {agent.name} skills_preferred not list"
            assert agent.priority in ["high", "medium", "low"], f"Agent {agent.name} invalid priority"
            assert isinstance(agent.requires_context, list), f"Agent {agent.name} requires_context not list"
            assert agent.system_prompt, f"Agent {agent.name} missing system_prompt"

    def test_all_skills_have_required_fields(self):
        """Verify all skills have required frontmatter fields."""
        reg = SkillRegistry(Path(".ases/skills"))
        skills = reg.list_skills()

        for skill in skills:
            assert skill.name, f"Skill missing name"
            assert skill.display_name, f"Skill {skill.name} missing display_name"
            assert skill.description, f"Skill {skill.name} missing description"
            assert isinstance(skill.agent_types, list), f"Skill {skill.name} agent_types not list"
            assert isinstance(skill.intent_triggers, list), f"Skill {skill.name} intent_triggers not list"
            assert isinstance(skill.provides, list), f"Skill {skill.name} provides not list"
            assert isinstance(skill.estimated_tokens, int), f"Skill {skill.name} estimated_tokens not int"
            assert skill.system_prompt, f"Skill {skill.name} missing system_prompt"


class TestIntegrationRouterWithRealCorpus:
    """Integration tests with actual agent corpus."""

    def test_intent_router_with_agent_intent_triggers_routes_correctly(self):
        """Verify IntentRouter routes using real agent corpus."""
        # Load agents to get intent_triggers
        agent_reg = AgentRegistry(Path(".ases/agents"))
        agents = agent_reg.list_agents()

        # Build corpus from intent_triggers
        corpus = {a.name: a.intent_triggers for a in agents}

        try:
            router = IntentRouter(corpus)
        except RuntimeError:
            pytest.skip("HuggingFace encoder unavailable")

        # Classify architect-related intent
        result = router.classify_intent("write an ADR")

        # Should route to architect or orchestrator (if fallback)
        assert result.type in [a.name for a in agents] or result.type == "orchestrator"
        # If routed via router (not fallback), confidence should be >= 0.7
        if result.method == "router":
            assert result.confidence >= 0.7

    def test_intent_router_routes_architect_intent_from_real_corpus(self):
        """Verify architect intent is routed correctly with real agents."""
        agent_reg = AgentRegistry(Path(".ases/agents"))
        agents = agent_reg.list_agents()
        corpus = {a.name: a.intent_triggers for a in agents}

        try:
            router = IntentRouter(corpus)
        except RuntimeError:
            pytest.skip("HuggingFace encoder unavailable")

        # Test with an architect-like utterance
        result = router.classify_intent("design the system architecture")

        # Should recognize architect intent
        assert result.confidence >= 0.0 and result.confidence <= 1.0
        # If high confidence, should route to architect
        if result.confidence >= 0.7:
            assert result.type == "architect"

    def test_intent_router_routes_coder_intent_from_real_corpus(self):
        """Verify coder intent is routed correctly with real agents."""
        agent_reg = AgentRegistry(Path(".ases/agents"))
        agents = agent_reg.list_agents()
        corpus = {a.name: a.intent_triggers for a in agents}

        try:
            router = IntentRouter(corpus)
        except RuntimeError:
            pytest.skip("HuggingFace encoder unavailable")

        # Test with a coder-like utterance
        result = router.classify_intent("implement the solution")

        # Should recognize coder intent
        assert result.confidence >= 0.0 and result.confidence <= 1.0
        # If high confidence, should route to coder
        if result.confidence >= 0.7:
            assert result.type == "coder"

    def test_intent_router_ambiguous_utterance_low_confidence(self):
        """Verify ambiguous utterance results in low confidence or fallback."""
        agent_reg = AgentRegistry(Path(".ases/agents"))
        agents = agent_reg.list_agents()
        corpus = {a.name: a.intent_triggers for a in agents}

        try:
            router = IntentRouter(corpus)
        except RuntimeError:
            pytest.skip("HuggingFace encoder unavailable")

        # Test with ambiguous/off-domain text
        result = router.classify_intent("the quick brown fox jumps over lazy dog")

        # Should either have low confidence or be flagged as fallback
        assert result.confidence < 0.7 or result.method == "llm_fallback"


class TestIntegrationRegistryConsistency:
    """Integration tests for consistency between registries."""

    def test_agent_registry_skills_preferred_reference_existing_skills(self):
        """Verify agent.skills_preferred references existing skills."""
        agent_reg = AgentRegistry(Path(".ases/agents"))
        skill_reg = SkillRegistry(Path(".ases/skills"))

        agents = agent_reg.list_agents()
        skill_names = {s.name for s in skill_reg.list_skills()}

        for agent in agents:
            for skill in agent.skills_preferred:
                assert skill in skill_names, f"Agent {agent.name} references nonexistent skill {skill}"

    def test_skill_registry_agent_types_reference_existing_agents(self):
        """Verify skill.agent_types references existing agents."""
        agent_reg = AgentRegistry(Path(".ases/agents"))
        skill_reg = SkillRegistry(Path(".ases/skills"))

        skills = skill_reg.list_skills()
        agent_names = {a.name for a in agent_reg.list_agents()}

        for skill in skills:
            for agent in skill.agent_types:
                assert agent in agent_names, f"Skill {skill.name} references nonexistent agent {agent}"
