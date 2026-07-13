"""GATE 5 VERIFIER: Import validation tests."""

import pytest
from .selector.engine import SelectorEngine, ExecutionPlan, ExecutionStep, build_execution_plan
from .executor.workflow_executor import WorkflowExecutor, InvalidStateTransition
from .executor.state_store import WorkflowStateStore, WorkflowRun
from .executor.step_runner import run_step, StepResult
from .executor.evidence_collector import Evidence, EvidenceType


class TestImports:
    """Verify all core modules import successfully."""

    def test_selector_engine_import(self):
        """SelectorEngine class imports."""
        assert SelectorEngine is not None
        assert hasattr(SelectorEngine, 'score_agents')
        assert hasattr(SelectorEngine, 'score_skills')
        assert hasattr(SelectorEngine, 'build_plan')

    def test_execution_plan_import(self):
        """ExecutionPlan dataclass imports."""
        assert ExecutionPlan is not None
        plan = ExecutionPlan(intent_class="test")
        assert plan.intent_class == "test"
        assert plan.steps == []

    def test_workflow_executor_import(self):
        """WorkflowExecutor class imports."""
        assert WorkflowExecutor is not None
        assert hasattr(WorkflowExecutor, 'execute')
        assert hasattr(WorkflowExecutor, 'resume')

    def test_workflow_state_store_import(self):
        """WorkflowStateStore class imports."""
        assert WorkflowStateStore is not None
        assert hasattr(WorkflowStateStore, 'create_run')
        assert hasattr(WorkflowStateStore, 'get_run')

    def test_evidence_contract_import(self):
        """Evidence dataclass imports."""
        assert Evidence is not None
        assert EvidenceType is not None
        assert hasattr(EvidenceType, 'AGENT_EXECUTION')
        assert hasattr(EvidenceType, 'APPROVAL_GATE')
        assert hasattr(EvidenceType, 'REJECTION')
        assert hasattr(EvidenceType, 'TIMEOUT')
        assert hasattr(EvidenceType, 'ERROR')

    def test_state_transition_validation(self):
        """State transition validation works."""
        executor = WorkflowExecutor(state_store=None, llm_client=None, agent_registry=None, skill_registry=None)

        # Valid transition
        executor._transition_state(None, "pending", "running")

        # Invalid transition should raise
        with pytest.raises(InvalidStateTransition):
            executor._transition_state(None, "complete", "running")

    def test_evidence_structure(self):
        """Evidence dataclass has all required fields."""
        ev = Evidence(
            step_id="step-1",
            step_name="architect",
            evidence_type=EvidenceType.AGENT_EXECUTION,
            system_prompt="prompt",
            user_message="message",
            agent_output="output",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            created_at="2026-07-07T00:00:00",
            status="success"
        )

        assert ev.step_id == "step-1"
        assert ev.step_name == "architect"
        assert ev.evidence_type == EvidenceType.AGENT_EXECUTION
        assert ev.total_tokens == 150

    def test_execution_step_structure(self):
        """ExecutionStep dataclass works."""
        step = ExecutionStep(
            step_id="step-1",
            agent_name="architect",
            skill_names=["repo-analysis", "adr-writer"],
            approval_gate=True
        )

        assert step.step_id == "step-1"
        assert step.agent_name == "architect"
        assert step.approval_gate is True
        assert len(step.skill_names) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
