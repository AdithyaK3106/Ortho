"""Internal types for architecture intelligence."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional


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


@dataclass
class Layer:
    """Detected architectural layer."""

    id: str
    name: str
    file_ids: list[str]
    depends_on: list[str]
    confidence: float


@dataclass
class Subsystem:
    """Detected architectural subsystem."""

    id: str
    name: str
    file_ids: list[str]
    coupling_score: float
    layer_id: Optional[str] = None


@dataclass
class ServiceBoundary:
    """Service boundary definition."""

    id: str
    name: str
    modules: list[str]


@dataclass
class ArchitectureModel:
    """Complete architecture model with style, layers, and subsystems."""

    repo_id: str
    style: ArchStyle
    style_confidence: float
    layers: list[Layer]
    subsystems: list[Subsystem]
    service_boundaries: list[ServiceBoundary] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    style_evidence: list[str] = field(default_factory=list)

    @property
    def evidence(self) -> list[str]:
        """Alias for style_evidence for backwards compatibility."""
        return self.style_evidence

    @evidence.setter
    def evidence(self, value: list[str]) -> None:
        """Alias for style_evidence for backwards compatibility."""
        self.style_evidence = value
