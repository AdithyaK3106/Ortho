"""Internal types for architecture intelligence."""

from dataclasses import dataclass, field
from typing import Literal


ArchStyle = Literal["layered", "hexagonal", "mvc", "microservices", "flat", "unknown"]


@dataclass
class DetectionMetrics:
    """Computed metrics for architecture detection."""

    layering_score: float  # 0.0 - 1.0 (how layered)
    cohesion_score: float  # 0.0 - 1.0 (internal coupling)
    modularity_score: float  # 0.0 - 1.0 (module independence)
    pattern_matches: dict[ArchStyle, float] = field(default_factory=dict)


@dataclass
class DetectionResult:
    """Result of architecture detection."""

    style: ArchStyle
    confidence: float  # 0.0 - 1.0
    evidence: list[str]  # Human-readable justifications
    alternative: ArchStyle | None = None
    alternative_confidence: float | None = None
