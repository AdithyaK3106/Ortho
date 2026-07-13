from dataclasses import dataclass, field


@dataclass
class ImplementationPath:
    name: str
    description: str
    affected_layers: list[str]
    effort: str
    risk: str
    dependencies_to_add: list[str] = field(default_factory=list)
    rationale: str = ""
    guardrail_violations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.effort not in ("low", "medium", "high"):
            raise ValueError("effort must be low, medium, or high")
        if self.risk not in ("low", "medium", "high"):
            raise ValueError("risk must be low, medium, or high")


@dataclass
class FeaturePlan:
    intent: str
    feature_type: str
    paths: list[ImplementationPath]
    recommended_path: str = ""

    def __post_init__(self) -> None:
        if len(self.paths) < 3:
            raise ValueError("Must provide at least 3 distinct paths")
