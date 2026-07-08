"""Hard unit tests for TokenBudget (spec.md AC1)."""

import pytest
import sys
from pathlib import Path

# Add src directory to path so token_optimizer can be imported
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

try:
    from token_optimizer.budget import TokenBudget, BudgetExceededError
except ImportError:
    TokenBudget = None
    BudgetExceededError = None


class TestTokenBudgetBasics:
    """Basic TokenBudget arithmetic tests."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_remaining_property(self):
        """AC1: remaining property returns total - used."""
        budget = TokenBudget(total=100, used=30, model="claude")
        assert budget.remaining == 70

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_remaining_zero(self):
        """Remaining is 0 when budget fully consumed."""
        budget = TokenBudget(total=50, used=50, model="claude")
        assert budget.remaining == 0

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_can_fit_positive(self):
        """AC1: can_fit(n) returns True when n <= remaining."""
        budget = TokenBudget(total=100, used=70, model="claude")
        assert budget.can_fit(30)
        assert budget.can_fit(25)
        assert budget.can_fit(1)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_can_fit_negative(self):
        """can_fit() returns False when tokens > remaining."""
        budget = TokenBudget(total=100, used=90, model="claude")
        assert not budget.can_fit(11)
        assert not budget.can_fit(100)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_can_fit_boundary_exact(self):
        """can_fit(remaining) returns True; can_fit(remaining+1) returns False."""
        budget = TokenBudget(total=100, used=75, model="claude")
        remaining = budget.remaining
        assert budget.can_fit(remaining)
        assert not budget.can_fit(remaining + 1)


class TestTokenBudgetConsume:
    """Hard consume() tests."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_increments_used(self):
        """AC1: consume(n) increments budget.used by n."""
        budget = TokenBudget(total=100, used=0, model="claude")
        budget.consume(30)
        assert budget.used == 30

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_in_place_mutation(self):
        """CRITICAL: consume() mutates the passed instance in place."""
        budget = TokenBudget(total=100, used=0, model="claude")
        budget_id = id(budget)
        budget.consume(50)
        assert id(budget) == budget_id
        assert budget.used == 50

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_exact_boundary(self):
        """Consume exactly remaining tokens."""
        budget = TokenBudget(total=100, used=90, model="claude")
        assert budget.remaining == 10
        budget.consume(10)
        assert budget.used == 100
        assert budget.remaining == 0

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_one_over_raises(self):
        """AC1: consume() raises BudgetExceededError if would overflow."""
        budget = TokenBudget(total=100, used=99, model="claude")
        with pytest.raises(BudgetExceededError):
            budget.consume(2)
        assert budget.used == 99

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_accumulates(self):
        """Multiple consume calls accumulate."""
        budget = TokenBudget(total=100, used=0, model="claude")
        budget.consume(30)
        budget.consume(20)
        budget.consume(40)
        assert budget.used == 90
        with pytest.raises(BudgetExceededError):
            budget.consume(11)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_exhaustion(self):
        """Consuming to exactly 0 remaining, then failing."""
        budget = TokenBudget(total=100, used=0, model="claude")
        budget.consume(100)
        assert budget.remaining == 0
        with pytest.raises(BudgetExceededError):
            budget.consume(1)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_consume_zero(self):
        """consume(0) is valid."""
        budget = TokenBudget(total=100, used=50, model="claude")
        budget.consume(0)
        assert budget.used == 50


class TestTokenBudgetIsolation:
    """Tests that separate budgets don't interfere."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_multiple_instances_isolated(self):
        """Two separate TokenBudget instances don't interfere."""
        budget1 = TokenBudget(total=100, used=0, model="claude")
        budget2 = TokenBudget(total=100, used=0, model="gpt-4")

        budget1.consume(50)
        assert budget1.used == 50
        assert budget2.used == 0


class TestTokenBudgetEdgeCases:
    """Edge case tests for TokenBudget."""

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_zero_total(self):
        """Budget with total=0 allows no consumption."""
        budget = TokenBudget(total=0, used=0, model="claude")
        assert budget.remaining == 0
        assert not budget.can_fit(1)
        with pytest.raises(BudgetExceededError):
            budget.consume(1)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_already_exhausted(self):
        """Budget created with used == total."""
        budget = TokenBudget(total=100, used=100, model="claude")
        assert budget.remaining == 0
        with pytest.raises(BudgetExceededError):
            budget.consume(1)

    @pytest.mark.skipif(TokenBudget is None, reason="TokenBudget not yet implemented")
    def test_token_budget_very_large_values(self):
        """TokenBudget handles very large token counts."""
        budget = TokenBudget(total=1_000_000_000, used=0, model="claude")
        budget.consume(500_000_000)
        assert budget.used == 500_000_000


class TestBudgetExceededError:
    """Tests for BudgetExceededError exception."""

    @pytest.mark.skipif(BudgetExceededError is None, reason="Not implemented")
    def test_budget_exceeded_error_is_exception(self):
        """BudgetExceededError is an Exception subclass."""
        assert issubclass(BudgetExceededError, Exception)

    @pytest.mark.skipif(BudgetExceededError is None, reason="Not implemented")
    def test_budget_exceeded_error_raised(self):
        """BudgetExceededError raised when consuming over budget."""
        budget = TokenBudget(total=100, used=95, model="claude")
        with pytest.raises(BudgetExceededError):
            budget.consume(10)
