"""Pillar 3: Architectural Intelligence"""

from .arch_detector import ArchitectureDetector, ArchitectureDetectionResult
from .layer_detector import LayerDetector
from .subsystem_detector import SubsystemDetector
from .model_store import ArchitectureModelStore
from .types import ArchStyle, ArchitectureModel, Layer, Subsystem
from .adr_tracker import ADRTracker, ADRStatus, SubsystemADRCoverage
from .reuse_detector import ReuseDetector, ReuseCluster
from .model_adapter import ArchModelAdapter

__all__ = [
    "ArchitectureDetector",
    "ArchitectureDetectionResult",
    "LayerDetector",
    "SubsystemDetector",
    "ArchitectureModelStore",
    "ArchStyle",
    "ArchitectureModel",
    "Layer",
    "Subsystem",
    "ADRTracker",
    "ADRStatus",
    "SubsystemADRCoverage",
    "ReuseDetector",
    "ReuseCluster",
    "ArchModelAdapter",
]
