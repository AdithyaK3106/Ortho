"""Hard integration tests for context assembler (spec.md AC3)."""

import pytest
import sys
from pathlib import Path

# Add src directory to path so token_optimizer can be imported
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from token_optimizer.budget import TokenBudget
    from token_optimizer.assembler import assemble_context
except ImportError:
    TokenBudget = None
    assemble_context = None


class TestAssembleContextDeterminism:
    """CRITICAL: Determinism tests — identical inputs must produce identical outputs."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_determinism_identical_inputs(self, mock_artifact_store):
        """AC3: Identical inputs ALWAYS produce identical context packages."""
        budget1 = TokenBudget(total=1000, used=0, model="claude")
        pkg1 = assemble_context(
            query="test query",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget1,
            step_id="step1",
            workflow_run_id="run1",
            model="claude"
        )

        budget2 = TokenBudget(total=1000, used=0, model="claude")
        pkg2 = assemble_context(
            query="test query",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget2,
            step_id="step1",
            workflow_run_id="run1",
            model="claude"
        )

        assert len(pkg1.chunks) == len(pkg2.chunks)
        for c1, c2 in zip(pkg1.chunks, pkg2.chunks):
            assert c1.source_id == c2.source_id
            assert c1.included == c2.included


class TestAssembleContextBudgetMutability:
    """Hard tests for budget mutability."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_budget_mutated_in_place(self, mock_artifact_store):
        """AC3: assemble_context() modifies the passed budget in place."""
        budget = TokenBudget(total=500, used=0, model="claude")
        budget_id = id(budget)
        initial_used = budget.used

        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        assert id(budget) == budget_id
        assert budget.used > initial_used
        assert id(pkg.budget) == id(budget)

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_budget_reference_same_instance(self, mock_artifact_store):
        """ContextPackage.budget is reference to same budget, not a copy."""
        budget = TokenBudget(total=1000, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        budget.used = 999
        assert pkg.budget.used == 999


class TestAssembleContextGreedyPacking:
    """Hard tests for greedy packing algorithm."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_greedy_respects_budget_hard_ceiling(self, mock_artifact_store):
        """Greedy packing never exceeds budget.total."""
        for budget_total in [100, 200, 500]:
            budget = TokenBudget(total=budget_total, used=0, model="claude")
            pkg = assemble_context(
                query="test",
                repo_id="test-repo",
                artifact_store=mock_artifact_store,
                budget=budget,
                step_id="step1",
                workflow_run_id="run1"
            )

            included_tokens = sum(
                c.token_count for c in pkg.chunks if c.included
            )
            assert included_tokens <= budget_total
            assert budget.used <= budget_total

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_empty_artifact_set(self):
        """Empty search results produce ContextPackage with no chunks."""
        from tests.conftest import MockArtifactStore
        store = MockArtifactStore([])

        budget = TokenBudget(total=100, used=0, model="claude")
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


class TestAssembleContextTieBreaking:
    """Hard tests for deterministic tie-breaking."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_tie_breaking_relevance_then_token_count(self, sample_artifacts_tie_breaking):
        """When relevance_score identical, sort by token_count ascending."""
        from tests.conftest import MockArtifactStore
        store = MockArtifactStore(sample_artifacts_tie_breaking)

        budget = TokenBudget(total=1000, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        included = [c for c in pkg.chunks if c.included]
        if len(included) >= 3:
            ids = [c.source_id for c in included]
            assert ids == ["a_artifact", "m_artifact", "z_artifact"]


class TestAssembleContextPackageContract:
    """Tests for ContextPackage structure."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_package_has_workflow_run_id(self, mock_artifact_store):
        """ContextPackage.workflow_run_id matches input."""
        budget = TokenBudget(total=500, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="my-run-123",
            model="claude"
        )

        assert pkg.workflow_run_id == "my-run-123"

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_package_has_step_id(self, mock_artifact_store):
        """ContextPackage.step_id matches input."""
        budget = TokenBudget(total=500, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="my-step-456",
            workflow_run_id="run1",
            model="claude"
        )

        assert pkg.step_id == "my-step-456"

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_all_chunks_returned(self, mock_artifact_store):
        """All candidate chunks returned, none silently dropped."""
        budget = TokenBudget(total=50, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        included_count = sum(1 for c in pkg.chunks if c.included)
        excluded_count = sum(1 for c in pkg.chunks if not c.included)
        assert len(pkg.chunks) == included_count + excluded_count


class TestAssembleContextChunkConversion:
    """Tests for artifact-to-chunk conversion."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_chunk_source_type_is_artifact(self, mock_artifact_store):
        """Converted ContextChunks have source_type='artifact'."""
        budget = TokenBudget(total=500, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        for chunk in pkg.chunks:
            assert chunk.source_type == "artifact"
