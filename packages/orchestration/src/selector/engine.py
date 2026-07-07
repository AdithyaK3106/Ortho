"""SelectorEngine: Pure Python agent and skill scoring, deterministic execution plan building."""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ExecutionStep:
    """Single step in an execution plan."""
    step_id: str
    agent_name: str
    skill_names: list[str]
    approval_gate: bool
    receives_from: Optional[str] = None
    produces: str = ""
    status: str = "pending"


@dataclass
class ExecutionPlan:
    """Ordered execution plan with agents, skills, and token estimates."""
    intent_class: str
    steps: list[ExecutionStep] = field(default_factory=list)
    total_estimated_tokens: int = 0
    human_approval_required: bool = False


# Workflow stage definitions per intent type (spec.md §1)
WORKFLOW_STAGES = {
    "feature_development": ["architect", "coder", "tester", "reviewer"],
    "bug_fix": ["debugger", "coder", "tester", "reviewer"],
    "refactor": ["architect", "coder", "reviewer"],
    "analysis": ["analyst"],
    "documentation": ["documenter"],
    "architecture_review": ["architect"],
}

# Approval-required agents (pause before execution)
APPROVAL_REQUIRED_AGENTS = {"architect", "reviewer", "debugger", "documenter"}

# Stage 99: custom agents (after all core stages)
CUSTOM_AGENT_STAGE = 99


class SelectorEngine:
    """Pure Python agent and skill scorer. Builds deterministic execution plans."""

    def __init__(self, agent_registry: Any, skill_registry: Any):
        """Initialize with agent and skill registries (from task-012)."""
        self.agents = agent_registry
        self.skills = skill_registry

    def score_agents(
        self,
        intent: Any,  # IntentClassification
        available_context: list[str],
    ) -> dict[str, float]:
        """Score all agents for this intent per spec.md §1.

        Formula:
        - Intent trigger match: +1.0
        - Priority weight: +{0.3|0.15|0.0}
        - Semantic similarity: +0.5 * sim_score
        - Context penalty: -0.2 per missing required context

        Returns: dict[agent_name → score], clipped to [0.0, ∞)
        """
        scores = {}

        for agent in self.agents.all_agents():
            score = 0.0

            # Intent trigger match: +1.0
            if intent.type in agent.intent_triggers:
                score += 1.0

            # Priority weight: +{0.3|0.15|0.0}
            priority_weights = {"high": 0.3, "medium": 0.15, "low": 0.0}
            score += priority_weights.get(agent.priority, 0.0)

            # Semantic similarity: +0.5 * sim_score (simple keyword match for now)
            sim = self._semantic_similarity(intent.raw_text if hasattr(intent, 'raw_text') else intent.type, agent.description)
            score += 0.5 * sim

            # Context penalty: -0.2 per missing required context
            for ctx in agent.requires_context:
                if ctx not in available_context:
                    score -= 0.2

            scores[agent.name] = max(0.0, score)

        return scores

    def score_skills(
        self,
        agent: Any,  # AgentManifest
        intent: Any,  # IntentClassification
        remaining_budget: int,
    ) -> dict[str, float]:
        """Score all skills for this agent per spec.md §1.

        Formula:
        - Agent type match: +0.8
        - Intent trigger match: +0.6
        - Agent preferred: +0.4
        - Hard exclude: score = 0.0 if tokens > budget

        Returns: dict[skill_name → score]
        """
        scores = {}

        for skill in self.skills.all_skills():
            # Hard exclude if over budget
            if skill.estimated_tokens > remaining_budget:
                scores[skill.name] = 0.0
                continue

            score = 0.0

            # Agent type match: +0.8
            if agent.name in skill.agent_types:
                score += 0.8

            # Intent trigger match: +0.6
            if intent.type in skill.intent_triggers:
                score += 0.6

            # Agent preferred: +0.4
            if skill.name in agent.skills_preferred:
                score += 0.4

            scores[skill.name] = score

        return scores

    def build_plan(
        self,
        intent: Any,  # IntentClassification
        available_context: list[str],
        token_budget: Any,  # TokenBudget
    ) -> ExecutionPlan:
        """Build deterministic execution plan from intent and scoring per spec.md §1.

        Algorithm:
        1. Score all agents
        2. Select agents with score ≥ 0.5
        3. Assign to workflow stages (earliest match for multiple stages)
        4. Order by (stage, score desc, name asc) — deterministic
        5. For each agent, score skills and select those with score > 0.3
        6. Sum token estimates
        7. Set human_approval_required based on intent type

        Returns: ExecutionPlan with ordered steps
        """
        # Step 1: Score agents
        agent_scores = self.score_agents(intent, available_context)

        # Step 2: Select agents with score ≥ 0.5
        selected_agents = {
            name: score for name, score in agent_scores.items()
            if score >= 0.5
        }

        # Step 3: Assign to stages and build step list
        stage_map = self._assign_agents_to_stages(selected_agents, intent.type)

        # Step 4: Order steps deterministically by (stage, score desc, name asc)
        sorted_steps = sorted(
            stage_map.items(),
            key=lambda x: (x[1]["stage"], -x[1]["score"], x[0])
        )

        # Step 5: Build ExecutionStep objects with skills
        plan = ExecutionPlan(
            intent_class=intent.type,
            human_approval_required=intent.type in {"feature_development", "bug_fix", "refactor"}
        )

        total_tokens = 0
        prev_step_id = None

        for idx, (agent_name, agent_info) in enumerate(sorted_steps):
            step_id = f"step-{idx + 1}"

            # Score and select skills for this agent
            agent = self.agents.get_agent(agent_name)
            remaining_budget = token_budget.remaining - total_tokens
            skill_scores = self.score_skills(agent, intent, remaining_budget)

            selected_skills = [
                name for name, score in skill_scores.items()
                if score > 0.3
            ]

            # Sum skill tokens
            skills_tokens = sum(
                self.skills.get_skill(skill_name).estimated_tokens
                for skill_name in selected_skills
            )
            total_tokens += skills_tokens

            step = ExecutionStep(
                step_id=step_id,
                agent_name=agent_name,
                skill_names=selected_skills,
                approval_gate=agent_name in APPROVAL_REQUIRED_AGENTS,
                receives_from=prev_step_id,
                produces=f"output_{step_id}"
            )

            plan.steps.append(step)
            prev_step_id = step_id

        plan.total_estimated_tokens = total_tokens
        return plan

    def _assign_agents_to_stages(self, selected_agents: dict[str, float], intent_type: str) -> dict[str, dict]:
        """Assign agents to workflow stages per spec.md §1.

        Returns: dict[agent_name → {stage, score}]
        """
        stages = WORKFLOW_STAGES.get(intent_type, [])
        stage_map = {}

        for agent_name, score in selected_agents.items():
            agent = self.agents.get_agent(agent_name)

            # Find earliest stage this agent matches
            stage = CUSTOM_AGENT_STAGE  # Default: custom agents go to Stage 99

            for idx, stage_name in enumerate(stages):
                if stage_name in agent.intent_triggers or agent_name == stage_name:
                    stage = idx + 1  # Stages are 1-indexed
                    break

            stage_map[agent_name] = {"stage": stage, "score": score}

        return stage_map

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """PLACEHOLDER: Token-based semantic similarity (Jaccard distance).

        This is an intentional placeholder implementation using simple Jaccard similarity on
        whitespace-separated tokens. It is NOT production-quality semantic similarity.

        Current behavior (Placeholder):
        - Splits text on whitespace (case-insensitive)
        - Returns Jaccard similarity: |intersection| / |union| of word sets
        - Deterministic for exact same input text
        - Fragile to punctuation, unicode, formatting variations

        Limitations (Why This is a Placeholder):
        - No word embeddings or semantic understanding
        - Sensitive to tokenization (punctuation treated as part of token)
        - No linguistic knowledge (synonyms, stemming, etc.)

        Future Implementation:
        Replace with embedding-based similarity in a future task
        (e.g., using sentence-transformers, HuggingFace models, or similar).
        This will provide actual semantic similarity rather than token overlap.

        Spec Compliance:
        This placeholder maintains the pure Python, deterministic design per spec.md §11.4.
        It correctly implements the required scoring formula while keeping the implementation
        simple and testable during Phase 1 (task-013).
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


def build_execution_plan(
    intent: Any,  # IntentClassification
    available_context: list[str],
    token_budget: Any,  # TokenBudget
    agent_registry: Any,  # AgentRegistry
    skill_registry: Any,  # SkillRegistry
) -> ExecutionPlan:
    """Build deterministic execution plan from intent.

    Convenience function using SelectorEngine.
    """
    engine = SelectorEngine(agent_registry, skill_registry)
    return engine.build_plan(intent, available_context, token_budget)
