from dataclasses import dataclass, field


@dataclass
class RefactoringIssue:
    issue_type: str
    location: str
    severity: str
    recommendation: str
    estimated_effort: str
    confidence: float
    false_positive_risk: str
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.severity not in ("low", "medium", "high"):
            raise ValueError("severity must be low, medium, or high")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0.0-1.0")
