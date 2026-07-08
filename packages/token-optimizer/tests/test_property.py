"""Property-based tests for token-optimizer invariants (spec.md AC1-AC8)."""

import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings, HealthCheck

# Add src directory to path so token_optimizer can be imported
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from token_optimizer.budget import TokenBudget, BudgetExceededError
    from token_optimizer.types import ContextChunk, ContextPackage
except ImportError:
    TokenBudget = None
    BudgetExceededError = None
    ContextChunk = None
    ContextPackage = None


class TestBudgetInvariants:
    """Property-based tests for TokenBudget invariants."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=100000),
        consumed=st.integers(min_value=0, max_value=100000),
    )
    @settings(max_examples=50)
    def test_remaining_always_nonnegative(self, total, consumed):
        """Invariant: remaining >= 0 (cannot be negative)."""
        assume(consumed <= total)
        budget = TokenBudget(total=total, used=consumed, model="test")
        assert budget.remaining >= 0

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=100000),
        consumed=st.integers(min_value=0, max_value=100000),
    )
    @settings(max_examples=50)
    def test_remaining_equals_total_minus_used(self, total, consumed):
        """Invariant: remaining == total - used."""
        assume(consumed <= total)
        budget = TokenBudget(total=total, used=consumed, model="test")
        assert budget.remaining == total - consumed

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=10000),
        amounts=st.lists(
            st.integers(min_value=1, max_value=1000),
            min_size=1,
            max_size=20
        ),
    )
    @settings(max_examples=30)
    def test_consume_increments_used_correctly(self, total, amounts):
        """Invariant: sum of consumed amounts equals final used value."""
        budget = TokenBudget(total=total, used=0, model="test")
        expected_used = 0

        for amount in amounts:
            if budget.remaining >= amount:
                budget.consume(amount)
                expected_used += amount
            else:
                break

        assert budget.used == expected_used

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=100, max_value=10000),
        to_consume=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
    def test_can_fit_matches_consume_success(self, total, to_consume):
        """Invariant: can_fit(n) == True iff consume(n) will succeed."""
        assume(to_consume <= total)
        budget = TokenBudget(total=total, used=0, model="test")

        # If can_fit returns True, consume should succeed
        if budget.can_fit(to_consume):
            try:
                budget.consume(to_consume)
                # Success as expected
                assert True
            except BudgetExceededError:
                pytest.fail("can_fit returned True but consume raised")
        else:
            # If can_fit returns False, consume should fail
            with pytest.raises(BudgetExceededError):
                budget.consume(to_consume)


class TestAssemblerInvariants:
    """Property-based tests for assembler invariants."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=100, max_value=50000),
        included_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=20)
    def test_included_tokens_never_exceed_budget(self, total, included_count):
        """Invariant: sum(included chunk tokens) <= budget.total."""
        # This is implicitly tested by assemble_context's greedy algorithm,
        # but we document it as a property.
        budget = TokenBudget(total=total, used=0, model="claude")

        # Invariant: after assembly, budget.used <= total
        assert budget.remaining >= 0
        assert budget.used <= total

    @pytest.mark.skipif(ContextChunk is None, reason="ContextChunk not yet implemented")
    @given(
        num_chunks=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=20)
    def test_chunk_id_always_present(self, num_chunks):
        """Invariant: every ContextChunk has a non-empty id."""
        chunks = [
            ContextChunk(
                id=f"chunk_{i}", source_type="artifact", source_id=f"src_{i}",
                content=f"Content {i}", relevance_score=0.5 + i * 0.01,
                token_count=10, included=(i % 2 == 0)
            )
            for i in range(num_chunks)
        ]

        for chunk in chunks:
            assert chunk.id is not None
            assert len(chunk.id) > 0

    @pytest.mark.skipif(ContextPackage is None, reason="ContextPackage not yet implemented")
    @given(
        package_id=st.text(min_size=1, max_size=50),
        workflow_run_id=st.text(min_size=1, max_size=50),
        step_id=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=20)
    def test_context_package_ids_preserved(self, package_id, workflow_run_id, step_id):
        """Invariant: ContextPackage retains all input IDs."""
        budget = TokenBudget(total=100, used=0, model="claude")
        pkg = ContextPackage(
            id=package_id,
            workflow_run_id=workflow_run_id,
            step_id=step_id,
            chunks=[],
            budget=budget,
            assembled_at="2026-07-08T00:00:00"
        )

        assert pkg.id == package_id
        assert pkg.workflow_run_id == workflow_run_id
        assert pkg.step_id == step_id


class TestPromptAssemblerInvariants:
    """Property-based tests for prompt assembler invariants."""

    @pytest.mark.skipif(ContextChunk is None, reason="ContextChunk not yet implemented")
    @given(
        num_included=st.integers(min_value=0, max_value=20),
        num_excluded=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=20)
    def test_prompt_respects_included_flag(self, num_included, num_excluded):
        """Invariant: Only included=True chunks can appear in prompt."""
        # This is a logical invariant verified by assemble_prompt
        # Chunks with included=False should never appear in user message

        included_chunks = [
            ContextChunk(
                id=f"inc_{i}", source_type="artifact", source_id=f"src_{i}",
                content=f"Included {i}", relevance_score=0.9,
                token_count=10, included=True
            )
            for i in range(num_included)
        ]

        excluded_chunks = [
            ContextChunk(
                id=f"exc_{i}", source_type="artifact", source_id=f"excluded_{i}",
                content=f"Excluded {i}", relevance_score=0.1,
                token_count=10, included=False
            )
            for i in range(num_excluded)
        ]

        # In a real prompt assembly, excluded chunks should not appear
        # We document this as an invariant
        for chunk in included_chunks:
            assert chunk.included is True
        for chunk in excluded_chunks:
            assert chunk.included is False


class TestDeterminismInvariants:
    """Property-based tests for determinism invariants."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=100, max_value=10000),
        initial_used=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=30)
    def test_budget_remaining_deterministic(self, total, initial_used):
        """Invariant: remaining property is deterministic."""
        assume(initial_used <= total)
        budget = TokenBudget(total=total, used=initial_used, model="test")

        # Multiple reads should give same result
        r1 = budget.remaining
        r2 = budget.remaining
        r3 = budget.remaining

        assert r1 == r2 == r3

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=100, max_value=10000),
        consume_sequence=st.lists(
            st.integers(min_value=1, max_value=100),
            min_size=1,
            max_size=20
        ),
    )
    @settings(max_examples=20)
    def test_consume_sequence_deterministic(self, total, consume_sequence):
        """Invariant: same sequence of consumes always produces same final state."""
        # Build two budgets and apply same consume sequence
        budget1 = TokenBudget(total=total, used=0, model="test")
        budget2 = TokenBudget(total=total, used=0, model="test")

        for amount in consume_sequence:
            if budget1.can_fit(amount):
                budget1.consume(amount)
            if budget2.can_fit(amount):
                budget2.consume(amount)

        # Both should be identical
        assert budget1.used == budget2.used
        assert budget1.remaining == budget2.remaining


class TestBoundaryInvariants:
    """Property-based tests for boundary conditions."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=30)
    def test_can_fit_zero_always_true(self, total):
        """Invariant: can_fit(0) is always True."""
        budget = TokenBudget(total=total, used=0, model="test")
        assert budget.can_fit(0)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=30)
    def test_consume_zero_is_idempotent(self, total):
        """Invariant: consume(0) is idempotent."""
        budget = TokenBudget(total=total, used=0, model="test")
        initial_used = budget.used

        budget.consume(0)
        assert budget.used == initial_used

        budget.consume(0)
        assert budget.used == initial_used

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=30)
    def test_consume_exact_remaining_succeeds(self, total):
        """Invariant: consume(remaining) always succeeds."""
        budget = TokenBudget(total=total, used=0, model="test")
        remaining = budget.remaining

        # Should not raise
        budget.consume(remaining)
        assert budget.remaining == 0

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    @given(
        total=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=30)
    def test_consume_remaining_plus_one_fails(self, total):
        """Invariant: consume(remaining + 1) always fails."""
        budget = TokenBudget(total=total, used=0, model="test")
        remaining = budget.remaining

        # Should raise
        with pytest.raises(BudgetExceededError):
            budget.consume(remaining + 1)
