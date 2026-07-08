"""Data types for architecture detection."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ArchStyle(str, Enum):
    """Architectural style classification."""
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    MVC = "mvc"
    MICROSERVICES = "microservices"
    FLAT = "flat"
    # Returned when no style reaches the evidence threshold — the detector
    # never guesses (see arch_detector._EVIDENCE_THRESHOLD).
    UNKNOWN = "unknown"


@dataclass
class ArchitectureDetectionResult:
    """Result of architecture pattern detection."""
    style: ArchStyle
    confidence: float
    evidence: list[str] = field(default_factory=list)
    alternative: Optional[ArchStyle] = None
    alternative_confidence: Optional[float] = None


@dataclass
class Layer:
    """Architectural layer."""
    id: str
    number: int
    name: str
    file_ids: list[str] = field(default_factory=list)
    depends_on: list[int] = field(default_factory=list)
    confidence: float = 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class Subsystem:
    """Detected subsystem/component."""
    id: str
    name: str
    file_ids: list[str] = field(default_factory=list)
    coupling_score: float = 0.0
    layer_id: Optional[str] = None


@dataclass
class ArchitectureModel:
    """Complete architecture model for a repository."""
    repo_id: str
    style: ArchStyle
    style_confidence: float
    layers: list[Layer] = field(default_factory=list)
    subsystems: list[Subsystem] = field(default_factory=list)
    detected_at: str = ""
    evidence: list[str] = field(default_factory=list)
