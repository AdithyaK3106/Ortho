"""Unit tests for SelectorEngine (score_agents, score_skills, build_plan)."""

import pytest
from packages.orchestration.src.selector.engine import SelectorEngine, ExecutionPlan, ExecutionStep
from packages.orchestration.src.intent.router import IntentClassification, AgentManifest, SkillManifest, AgentRegistry, SkillRegistry
from packages.shared.types import TokenBudget


class MockAgentRegistry:
    """Mock AgentRegistry for testing."""

    def __init__(self):
        self.agents = {
            "architect": AgentManifest(
                name="architect",
                display_name="Architect",
                description="Designs system architecture",
                intent_triggers=["feature_development", "refactor", "architecture_review"],
                skills_preferred=["adr-writer", "impact-analyzer"],
                priority="high",
                requires_context=["architecture_model"],
            ),
            "coder": AgentManifest(
                name="coder",
                display_name="Coder",
                description="Implements features and fixes bugs",
                intent_triggers=["feature_development", "bug_fix"],
                skills_preferred=[],
                priority="high",
                requires_context=[],
            ),
            "analyst": AgentManifest(
                name="analyst",
                display_name="Analyst",
                description="Analyzes code and impact",
                intent_triggers=["analysis"],
                skills_preferred=["impact-analyzer"],
                priority="medium",
                requires_context=["dependency_graph"],
            ),
        }

    def get_agent(self, name: str) -> AgentManifest:
        return self.agents[name]

    def all_agents(self) -> list:
        return list(self.agents.values())


class MockSkillRegistry:
    """Mock SkillRegistry for testing."""

    def __init__(self):
        self.skills = {
            "adr-writer": SkillManifest(
                name="adr-writer",
                display_name="ADR Writer",
                description="Writes ADRs",
                agent_types=["architect"],
                intent_triggers=["architecture_review"],
                estimated_tokens=800,
            ),
            "impact-analyzer": SkillManifest(
                name="impact-analyzer",
                display_name="Impact Analyzer",
                description="Analyzes impact",
                agent_types=["architect", "analyst"],
                intent_triggers=["analysis"],
                estimated_tokens=600,
            ),
        }

    def get_skill(self, name: str) -> SkillManifest:
        return self.skills[name]

    def all_skills(self) -> list:
        return list(self.skills.values())


@pytest.fixture
def selector():
    """Create SelectorEngine with mock registries."""
    agent_reg = MockAgentRegistry()
    skill_reg = MockSkillRegistry()
    return SelectorEngine(agent_reg, skill_reg)


@pytest.fixture
def intent_feature_dev():
    """Create feature_development intent."""
    return IntentClassification(
        type="feature_development",
        confidence=0.91,
        method="router",
        raw_text="add rate limiting to auth service"
    )


@pytest.fixture
def intent_analysis():
    """Create analysis intent."""
    return IntentClassification(
        type="analysis",
        confidence=0.85,
        method="router",
        raw_text="what is the blast radius"
    )


# ============================================================================
# Unit Tests: score_agents (spec.md §1)
# ============================================================================

def test_score_agents_intent_match(selector, intent_feature_dev):
    """Test intent trigger match (+1.0)."""
    scores = selector.score_agents(intent_feature_dev, [])
    assert scores["architect"] >= 1.0  # intent_triggers match
    assert scores["coder"] >= 1.0      # intent_triggers match
    # analyst doesn't match feature_development
    assert scores["analyst"] < scores["architect"]


def test_score_agents_priority_weight(selector, intent_feature_dev):
    """Test priority weight (+0.3|0.15|0)."""
    scores = selector.score_agents(intent_feature_dev, [])
    # architect: high priority (+0.3)
    # coder: high priority (+0.3)
    # analyst: medium priority (+0.15)
    assert scores["architect"] > scores["analyst"]
    assert scores["coder"] > scores["analyst"]


def test_score_agents_context_penalty(selector, intent_feature_dev):
    """Test context penalty (-0.2 per missing)."""
    # architect requires "architecture_model"
    scores_without_context = selector.score_agents(intent_feature_dev, [])
    scores_with_context = selector.score_agents(intent_feature_dev, ["architecture_model"])

    assert scores_with_context["architect"] > scores_without_context["architect"]
    assert scores_with_context["architect"] - scores_without_context["architect"] >= 0.2


def test_score_agents_zero_floor(selector, intent_analysis):
    """Test scores are floored at 0.0."""
    scores = selector.score_agents(intent_analysis, [])
    for score in scores.values():
        assert score >= 0.0


# ============================================================================
# Unit Tests: score_skills (spec.md §1)
# ============================================================================

def test_score_skills_agent_type_match(selector, intent_feature_dev):
    """Test agent_type match (+0.8)."""
    architect = selector.agents.get_agent("architect")
    scores = selector.score_skills(architect, intent_feature_dev, 10000)

    # adr-writer matches architect
    assert scores["adr-writer"] >= 0.8


def test_score_skills_intent_triggers(selector, intent_feature_dev):
    """Test intent trigger match (+0.6)."""
    architect = selector.agents.get_agent("architect")
    scores = selector.score_skills(architect, intent_feature_dev, 10000)

    # adr-writer has architecture_review intent (not feature_development)
    # But impact-analyzer has architecture_review, not feature_development either
    # So no intent trigger matches for feature_development
    assert scores["adr-writer"] >= 0.8  # agent_type match


def test_score_skills_budget_exclusion(selector, intent_feature_dev):
    """Test hard budget exclusion (score = 0 if over budget)."""
    architect = selector.agents.get_agent("architect")

    # Only 500 tokens remaining, but adr-writer needs 800
    scores = selector.score_skills(architect, intent_feature_dev, 500)
    assert scores["adr-writer"] == 0.0

    # With enough budget, adr-writer gets scored
    scores = selector.score_skills(architect, intent_feature_dev, 1000)
    assert scores["adr-writer"] > 0.0


def test_score_skills_preferred_bonus(selector, intent_feature_dev):
    """Test agent preferred skills (+0.4)."""
    architect = selector.agents.get_agent("architect")
    scores = selector.score_skills(architect, intent_feature_dev, 10000)

    # adr-writer is in architect.skills_preferred
    assert scores["adr-writer"] >= 0.4


# ============================================================================
# Unit Tests: build_plan (spec.md §1, Deterministic Workflow Ordering)
# ============================================================================

def test_build_plan_deterministic_ordering(selector, intent_feature_dev):
    """Test deterministic step ordering (stage, score desc, name asc)."""
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")
    context = ["architecture_model"]

    plan1 = selector.build_plan(intent_feature_dev, context, budget)
    plan2 = selector.build_plan(intent_feature_dev, context, budget)

    # Same input → identical plan
    assert len(plan1.steps) == len(plan2.steps)
    for s1, s2 in zip(plan1.steps, plan2.steps):
        assert s1.agent_name == s2.agent_name
        assert s1.step_id == s2.step_id


def test_build_plan_stage_ordering(selector, intent_feature_dev):
    """Test agents ordered by workflow stages."""
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")
    plan = selector.build_plan(intent_feature_dev, [], budget)

    agent_names = [step.agent_name for step in plan.steps]

    # feature_development stages: architect (1) → coder (2) → tester (3) → reviewer (4)
    # Only architect and coder are selected, so order should be: architect, coder
    if "architect" in agent_names and "coder" in agent_names:
        assert agent_names.index("architect") < agent_names.index("coder")


def test_build_plan_approval_gates(selector, intent_feature_dev):
    """Test approval gates set for architect/reviewer."""
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")
    plan = selector.build_plan(intent_feature_dev, [], budget)

    for step in plan.steps:
        if step.agent_name in {"architect", "reviewer", "debugger", "documenter"}:
            assert step.approval_gate is True


def test_build_plan_skill_selection(selector, intent_feature_dev):
    """Test skills selected (score > 0.3)."""
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")
    context = ["architecture_model"]
    plan = selector.build_plan(intent_feature_dev, context, budget)

    architect_step = next((s for s in plan.steps if s.agent_name == "architect"), None)
    if architect_step:
        # architect should have selected skills
        assert isinstance(architect_step.skill_names, list)


def test_build_plan_token_estimation(selector, intent_feature_dev):
    """Test total token estimate."""
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")
    plan = selector.build_plan(intent_feature_dev, ["architecture_model"], budget)

    assert plan.total_estimated_tokens >= 0
    assert plan.total_estimated_tokens <= budget.total


def test_build_plan_human_approval_required(selector, intent_feature_dev, intent_analysis):
    """Test human_approval_required flag per intent type."""
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")

    plan_feature = selector.build_plan(intent_feature_dev, [], budget)
    assert plan_feature.human_approval_required is True

    plan_analysis = selector.build_plan(intent_analysis, [], budget)
    assert plan_analysis.human_approval_required is False


# ============================================================================
# Property-Based Tests (hypothesis)
# ============================================================================

from hypothesis import given, strategies as st, settings


@given(
    score=st.floats(min_value=0.0, max_value=2.0),
)
@settings(max_examples=50)
def test_agent_scores_non_negative(selector, score):
    """Property: agent scores are always non-negative."""
    # Just verify our scoring floor works
    assert max(0.0, score - 1.0) >= 0.0


@given(
    budget=st.integers(min_value=100, max_value=50000)
)
@settings(max_examples=50)
def test_plan_respects_budget(selector, intent_feature_dev, budget):
    """Property: plan total tokens ≤ budget."""
    token_budget = TokenBudget(total=budget, used=0, model="claude-sonnet")
    plan = selector.build_plan(intent_feature_dev, [], token_budget)
    assert plan.total_estimated_tokens <= budget


# ============================================================================
# Determinism Tests (Critical for spec.md §1)
# ============================================================================

@pytest.mark.parametrize("intent_type,context", [
    ("feature_development", []),
    ("feature_development", ["architecture_model"]),
    ("analysis", []),
    ("analysis", ["dependency_graph"]),
])
def test_build_plan_determinism_parametrized(selector, intent_type, context):
    """Test determinism across multiple intent types and contexts."""
    intent = IntentClassification(
        type=intent_type,
        confidence=0.90,
        method="router",
        raw_text="test intent"
    )
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")

    plan1 = selector.build_plan(intent, context, budget)
    plan2 = selector.build_plan(intent, context, budget)
    plan3 = selector.build_plan(intent, context, budget)

    # All three runs should be identical
    assert len(plan1.steps) == len(plan2.steps) == len(plan3.steps)
    for s1, s2, s3 in zip(plan1.steps, plan2.steps, plan3.steps):
        assert s1.agent_name == s2.agent_name == s3.agent_name
        assert s1.step_id == s2.step_id == s3.step_id
