"""Edge case and boundary condition tests for token-optimizer."""

import pytest
import sys
from pathlib import Path

# Add src directory to path so token_optimizer can be imported
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from token_optimizer.budget import TokenBudget, BudgetExceededError
    from token_optimizer.types import ContextPackage, ContextChunk
    from token_optimizer.assembler import assemble_context
    from token_optimizer.prompt import assemble_prompt
except ImportError:
    TokenBudget = None
    BudgetExceededError = None
    ContextPackage = None
    ContextChunk = None
    assemble_context = None
    assemble_prompt = None


class TestTokenBudgetEdgeCases:
    """Edge cases for TokenBudget."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_zero_total(self):
        """Budget.total = 0 allows no consumption."""
        budget = TokenBudget(total=0, used=0, model="claude")
        assert budget.remaining == 0
        assert not budget.can_fit(1)
        with pytest.raises(BudgetExceededError):
            budget.consume(1)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_created_exhausted(self):
        """Budget created with used == total."""
        budget = TokenBudget(total=100, used=100, model="claude")
        assert budget.remaining == 0
        with pytest.raises(BudgetExceededError):
            budget.consume(1)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_huge_values(self):
        """Very large token budgets handled correctly."""
        huge = 1_000_000_000_000  # 1 trillion
        budget = TokenBudget(total=huge, used=500_000_000_000, model="claude")
        assert budget.remaining == 500_000_000_000
        budget.consume(500_000_000_000)
        assert budget.remaining == 0

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_model_field_empty_string(self):
        """Model field can be empty string (edge case)."""
        budget = TokenBudget(total=100, used=0, model="")
        assert budget.model == ""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_isolation_no_global_state(self):
        """Multiple budgets don't share state."""
        budgets = [
            TokenBudget(total=100, used=0, model="m1"),
            TokenBudget(total=100, used=0, model="m2"),
            TokenBudget(total=100, used=0, model="m3"),
        ]

        budgets[0].consume(33)
        budgets[1].consume(66)
        budgets[2].consume(99)

        assert budgets[0].used == 33
        assert budgets[1].used == 66
        assert budgets[2].used == 99


class TestAssemblerEdgeCases:
    """Edge cases for assembler."""

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_empty_search_results(self):
        """Empty artifact list returns empty ContextPackage."""
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

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_zero_budget(self):
        """Zero budget → no chunks included."""
        from tests.conftest import MockArtifactStore, MockArtifact

        budget = TokenBudget(total=0, used=0, model="claude")
        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=MockArtifactStore([
                MockArtifact(id="a1", estimated_tokens=1, relevance_score=0.9, content="test")
            ]),
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        # All chunks should be present but not included
        for chunk in pkg.chunks:
            assert chunk.included is False

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_single_chunk_exactly_fits(self):
        """Single chunk with tokens == budget.total."""
        from tests.conftest import MockArtifactStore, MockArtifact

        store = MockArtifactStore([
            MockArtifact(id="fit_exactly", content="content",
                         estimated_tokens=100, relevance_score=0.9)
        ])
        budget = TokenBudget(total=100, used=0, model="claude")

        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        # Chunk should be included
        assert len(pkg.chunks) > 0
        assert pkg.chunks[0].included

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_single_chunk_exceeds_budget(self):
        """Single chunk with tokens > budget.total → not included."""
        from tests.conftest import MockArtifactStore, MockArtifact

        store = MockArtifactStore([
            MockArtifact(id="oversized", content="x" * 10000,
                         estimated_tokens=5000, relevance_score=0.9)
        ])
        budget = TokenBudget(total=100, used=0, model="claude")

        pkg = assemble_context(
            query="test",
            repo_id="test-repo",
            artifact_store=store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )

        # Chunk should be present but NOT included
        assert len(pkg.chunks) == 1
        assert pkg.chunks[0].included is False


class TestPromptAssemblerEdgeCases:
    """Edge cases for prompt assembly."""

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_prompt_no_included_chunks(self, mock_agent, mock_skills):
        """No included chunks → empty user message."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        chunks = [
            ContextChunk(
                id="ch1", source_type="artifact", source_id="s1",
                content="content", relevance_score=0.9,
                token_count=10, included=False
            ),
        ]
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=chunks, budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        assert user_msg == ""

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_prompt_chunk_with_empty_content(self, mock_agent, mock_skills):
        """Chunk with empty content handled correctly."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        chunk = ContextChunk(
            id="ch1", source_type="artifact", source_id="s1",
            content="", relevance_score=0.9,
            token_count=0, included=True
        )
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=[chunk], budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        # Header should be there even with empty content
        assert "[artifact:s1]" in user_msg

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_prompt_chunk_with_newlines_in_content(self, mock_agent, mock_skills):
        """Content with embedded newlines preserved."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        chunk = ContextChunk(
            id="ch1", source_type="artifact", source_id="s1",
            content="line1\nline2\nline3", relevance_score=0.9,
            token_count=10, included=True
        )
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=[chunk], budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        assert "line1\nline2\nline3" in user_msg

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_prompt_very_large_content(self, mock_agent, mock_skills):
        """Very large chunk content handled (no truncation by assembler)."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        large_content = "x" * 100_000  # 100KB of content
        chunk = ContextChunk(
            id="ch1", source_type="artifact", source_id="s1",
            content=large_content, relevance_score=0.9,
            token_count=50000, included=True
        )
        budget = TokenBudget(total=100_000, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=[chunk], budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        # Entire content should be present (no truncation)
        assert large_content in user_msg

    @pytest.mark.skipif(assemble_prompt is None, reason="prompt assembler not implemented")
    def test_prompt_special_characters_preserved(self, mock_agent, mock_skills):
        """Special characters and escapes preserved."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        special = 'code: `x = 1` <tag> & "quotes" \\n \\t'
        chunk = ContextChunk(
            id="ch1", source_type="artifact", source_id="s1",
            content=special, relevance_score=0.9,
            token_count=10, included=True
        )
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=[chunk], budget=budget, assembled_at=now
        )

        _, user_msg = assemble_prompt(pkg, step=None, agent=mock_agent, skills=[])

        assert special in user_msg


class TestTypeHandlingEdgeCases:
    """Edge cases for type handling."""

    @pytest.mark.skipif(ContextChunk is None, reason="ContextChunk not implemented")
    def test_context_chunk_relevance_score_extremes(self):
        """ContextChunk handles relevance_score extremes (0.0 and 1.0)."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        budget = TokenBudget(total=100, used=0, model="claude")

        chunk1 = ContextChunk(
            id="ch1", source_type="artifact", source_id="s1",
            content="content", relevance_score=0.0,
            token_count=10, included=True
        )
        chunk2 = ContextChunk(
            id="ch2", source_type="artifact", source_id="s2",
            content="content", relevance_score=1.0,
            token_count=10, included=True
        )

        assert chunk1.relevance_score == 0.0
        assert chunk2.relevance_score == 1.0

    @pytest.mark.skipif(ContextPackage is None, reason="ContextPackage not implemented")
    def test_context_package_iso_timestamp_format(self):
        """ContextPackage.assembled_at is valid ISO 8601."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id="pkg1", workflow_run_id="run1", step_id="step1",
            chunks=[], budget=budget, assembled_at=now
        )

        # Should be parseable
        try:
            datetime.fromisoformat(pkg.assembled_at.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid ISO timestamp: {pkg.assembled_at}")

    @pytest.mark.skipif(ContextChunk is None, reason="ContextChunk not implemented")
    def test_context_chunk_all_source_types(self):
        """ContextChunk handles all documented source_types."""
        from datetime import datetime

        now = datetime.utcnow().isoformat()
        budget = TokenBudget(total=100, used=0, model="claude")

        for source_type in ["symbol", "artifact", "git", "architecture"]:
            chunk = ContextChunk(
                id=f"ch_{source_type}", source_type=source_type, source_id="s1",
                content="content", relevance_score=0.9,
                token_count=10, included=True
            )
            assert chunk.source_type == source_type


class TestConcurrencyHints:
    """Tests hinting at concurrency-related edge cases (not enforced)."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_budget_no_thread_safety_guarantee(self):
        """Document: TokenBudget has no thread-safety guarantees."""
        budget = TokenBudget(total=100, used=0, model="claude")

        # Sequential operations should work fine
        budget.consume(25)
        budget.consume(25)
        budget.consume(25)
        budget.consume(25)

        assert budget.used == 100

        # Concurrent access is caller's responsibility (not tested here)
        # This test just documents the expected behavior

    @pytest.mark.skipif(assemble_context is None, reason="assembler not implemented")
    def test_assemble_context_same_budget_sequential_calls(self, mock_artifact_store):
        """Sequential calls with same budget accumulate used tokens."""
        budget = TokenBudget(total=1000, used=0, model="claude")

        # First call
        pkg1 = assemble_context(
            query="test1",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step1",
            workflow_run_id="run1"
        )
        used_after_first = budget.used

        # Second call with same budget (caller must manage lifecycle)
        pkg2 = assemble_context(
            query="test2",
            repo_id="test-repo",
            artifact_store=mock_artifact_store,
            budget=budget,
            step_id="step2",
            workflow_run_id="run1"
        )
        used_after_second = budget.used

        # Second call should add to used (caller's responsibility if not desired)
        assert used_after_second >= used_after_first


# Helper: Mock classes for edge case tests (replicate from conftest if needed)
try:
    from tests.conftest import MockArtifact, MockArtifactStore
except ImportError:
    pass
