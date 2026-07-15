"""Adapts a real scanned ArchitectureModel to feature_planner's
ArchitectureModel Protocol (get_style() -> str)."""

from __future__ import annotations

from arch_intelligence.types import ArchitectureModel


class FeaturePlannerArchModelAdapter:
    def __init__(self, arch_model: ArchitectureModel) -> None:
        self._arch_model = arch_model

    def get_style(self) -> str:
        return str(self._arch_model.style.value)
