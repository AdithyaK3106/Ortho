from dataclasses import dataclass, field


@dataclass
class Recommendation:
    title: str
    description: str
    source: str
    effort: str
    risk: str
    confidence: float
    suggested_fix: str
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0.0-1.0")
        if self.effort not in ("low", "medium", "high"):
            raise ValueError("effort must be low, medium, or high")
        if self.risk not in ("low", "medium", "high"):
            raise ValueError("risk must be low, medium, or high")


@dataclass
class Decision:
    intent: str
    options: list[Recommendation]
    recommended_option: Recommendation
    reasoning: str
    confidence: float

    def __post_init__(self) -> None:
        if len(self.options) < 1:
            raise ValueError("Must have at least 1 option")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0.0-1.0")
