"""TokenBudget: Token allocation and consumption tracking per spec.md AC1."""

from dataclasses import dataclass


class BudgetExceededError(Exception):
    """Raised when TokenBudget.consume() would exceed total."""
    pass


@dataclass
class TokenBudget:
    """Tracks token budget allocation and consumption.

    Mutable by design: consume() modifies used in place.
    Caller is responsible for budget lifecycle (create fresh or reset per step).
    """
    total: int
    used: int
    model: str

    @property
    def remaining(self) -> int:
        """Return remaining tokens in budget."""
        return self.total - self.used

    def can_fit(self, tokens: int) -> bool:
        """Check if tokens fit in remaining budget.

        Args:
            tokens: Number of tokens to check

        Returns:
            True if tokens <= remaining, False otherwise
        """
        return tokens <= self.remaining

    def consume(self, tokens: int) -> None:
        """Consume tokens from budget or raise BudgetExceededError.

        Modifies self.used in place (mutable semantics).

        Args:
            tokens: Number of tokens to consume

        Raises:
            BudgetExceededError: If used + tokens > total
        """
        if not self.can_fit(tokens):
            raise BudgetExceededError(
                f"Cannot consume {tokens} tokens; only {self.remaining} remaining "
                f"(total: {self.total}, used: {self.used})"
            )
        self.used += tokens
