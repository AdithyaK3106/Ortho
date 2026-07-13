from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class EdgeType(Enum):
    DIRECT_CALL = "direct_call"
    TRANSITIVE_CALL = "transitive_call"
    IMPORT = "import"
    STAR_IMPORT = "star_import"
    DYNAMIC_IMPORT = "dynamic_import"
    CONDITIONAL_IMPORT = "conditional_import"


@dataclass
class ImpactEdge:
    source: str
    target: str
    edge_type: EdgeType
    distance: int

    def __hash__(self) -> int:
        return hash((self.source, self.target, self.edge_type, self.distance))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImpactEdge):
            return NotImplemented
        return (
            self.source == other.source
            and self.target == other.target
            and self.edge_type == other.edge_type
            and self.distance == other.distance
        )


@dataclass
class ImpactPrediction:
    changed_file: str
    affected_modules: list[str]
    affected_functions: list[str]
    cascade_risk: str
    confidence: float
    reasoning: str
    evidence: list[ImpactEdge] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.cascade_risk not in ("low", "medium", "high"):
            raise ValueError("cascade_risk must be low, medium, or high")
