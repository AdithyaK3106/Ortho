from dataclasses import dataclass, field


@dataclass
class GuardrailViolation:
    rule_id: str
    severity: str
    location: str
    message: str
    suggested_fix: str
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.severity not in ("error", "warning"):
            raise ValueError("severity must be error or warning")
