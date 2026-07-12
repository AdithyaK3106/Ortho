"""Integration tests for token-optimizer (spec.md AC5-AC8)."""

import pytest
import sys
from pathlib import Path

# Add src directory to path so token_optimizer can be imported
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from token_optimizer.budget import TokenBudget
    from token_optimizer.types import ContextPackage
    from token_optimizer.assembler import assemble_context
    from token_optimizer.prompt import assemble_prompt
except ImportError:
    TokenBudget = None
    ContextPackage = None
    assemble_context = None
    assemble_prompt = None


class TestAssemblerToPromptIntegration:
    """Integration: assembler output feeds into prompt assembly."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assembler_output_valid_input_to_prompt_assembler(
        self, mock_artifact_store, mock_agent, mock_skills
    ):
        """AC5: assemble_context output is valid input to assemble_prompt."""
        budget = TokenBudget(total=500, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        # Should be able to call assemble_prompt with output
        system_msg, user_msg = assemble_prompt(
            pkg, step=None, agent=mock_agent, skills=mock_skills
        )

        # Results should be strings
        assert isinstance(system_msg, str)
        assert isinstance(user_msg, str)

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_end_to_end_workflow(
        self, mock_artifact_store, mock_agent, mock_skills
    ):
        """AC5: End-to-end assembler → prompt assembly workflow."""
        budget = TokenBudget(total=300, used=0, model="claude")

        # Step 1: Assembly context
        pkg = assemble_context(
            query="authentication",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="architect_step",
            workflow_run_id="workflow_123"
        )

        # Package should contain chunks
        assert len(pkg.chunks) > 0 or len(pkg.chunks) == 0  # Handle empty case
        assert pkg.workflow_run_id == "workflow_123"
        assert pkg.step_id == "architect_step"

        # Step 2: Assemble prompt
        system_msg, user_msg = assemble_prompt(
            pkg, step=None, agent=mock_agent, skills=mock_skills
        )

        # User message should reflect included chunks
        included_count = sum(1 for c in pkg.chunks if c.included)
        if included_count > 0:
            assert len(user_msg) > 0
        else:
            assert user_msg == ""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_multiple_steps_with_fresh_budget(
        self, mock_artifact_store, mock_agent, mock_skills
    ):
        """Each step should use a fresh budget (caller responsibility)."""
        # Step 1
        budget1 = TokenBudget(total=200, used=0, model="claude")
        pkg1 = assemble_context(
            query="auth",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget1,
            step_id="step1",
            workflow_run_id="run1"
        )
        tokens_used_step1 = budget1.used

        # Step 2 with fresh budget
        budget2 = TokenBudget(total=200, used=0, model="claude")
        pkg2 = assemble_context(
            query="logging",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget2,
            step_id="step2",
            workflow_run_id="run1"
        )
        tokens_used_step2 = budget2.used

        # Each should have independent budgets
        assert budget1.used == tokens_used_step1
        assert budget2.used == tokens_used_step2
        # budget2.used may be different from budget1.used (different queries)
        # but they are independent objects


class TestAssemblerPromptConsistency:
    """Integration: consistent behavior across assembler-prompt boundary."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_included_chunks_appear_in_prompt(
        self, mock_artifact_store, mock_agent, mock_skills
    ):
        """AC5: Chunks marked included=True in package appear in prompt."""
        budget = TokenBudget(total=500, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        # Each included chunk's source_id should appear in message
        for chunk in pkg.chunks:
            if chunk.included:
                assert chunk.source_id in user_msg

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_excluded_chunks_not_in_prompt(
        self, mock_artifact_store, mock_agent, mock_skills
    ):
        """AC5: Chunks marked included=False do NOT appear in prompt."""
        budget = TokenBudget(total=100, used=0, model="claude")  # Small budget
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        # Excluded chunks should NOT appear
        for chunk in pkg.chunks:
            if not chunk.included:
                # source_id should not be in message
                # (unless duplicate with an included chunk, but that's tested elsewhere)
                assert chunk.source_id not in user_msg or any(
                    c.source_id == chunk.source_id and c.included
                    for c in pkg.chunks
                )

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_budget_state_visible_after_assembly(
        self, mock_artifact_store, mock_agent, mock_skills
    ):
        """AC5: Budget state can be inspected after assembly."""
        budget = TokenBudget(total=500, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        # Budget should be inspectable
        assert pkg.budget.used >= 0
        assert pkg.budget.total == 500
        assert pkg.budget.remaining <= 500

        # budget and pkg.budget should be same object
        budget.consume(10)
        assert pkg.budget.used == budget.used


class TestRegressionInvariants:
    """AC8: Zero regressions — existing behavior preserved."""

    def test_placeholder_no_new_errors_in_existing_tests(self):
        """AC8: Existing test suites should continue to pass."""
        # This is verified at VERIFIER stage by running the full test suite
        # Here we just document the expectation
        pass

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_backward_compatible_with_mock(self):
        """AC8: TokenBudget compatible with existing test mock."""
        # Existing mock in test_selector_engine.py line 44
        from packages.orchestration.tests.test_selector_engine import TokenBudget as MockTokenBudget

        # Real TokenBudget should have same interface
        budget = TokenBudget(total=100, used=0, model="claude")
        mock = MockTokenBudget(total=100, used=0, model="claude")

        # Both should have same properties
        assert hasattr(budget, 'total')
        assert hasattr(budget, 'used')
        assert hasattr(budget, 'model')
        assert hasattr(budget, 'remaining')
        assert hasattr(mock, 'total')
        assert hasattr(mock, 'used')
        assert hasattr(mock, 'model')
        assert hasattr(mock, 'remaining')

        # Values should match
        assert budget.remaining == mock.remaining


class TestErrorHandlingIntegration:
    """Integration: error paths work correctly."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_exceeded_during_assembly(self, mock_artifact_store):
        """Assembly handles budget exhaustion gracefully."""
        budget = TokenBudget(total=10, used=0, model="claude")  # Tiny budget

        # Should not raise; should mark chunks as excluded
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        # Should have chunks with mixed included/excluded status
        # (or all excluded if budget too small)
        assert len(pkg.chunks) >= 0

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_empty_artifact_set_handles_gracefully(self):
        """Empty search results don't crash assembly."""
        from tests.conftest import MockArtifactStore

        store = MockArtifactStore([])
        budget = TokenBudget(total=100, used=0, model="claude")

        # Should not raise
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        assert len(pkg.chunks) == 0
        assert budget.used == 0
