"""Query adapter over ArchitectureModel for downstream protocol consumers.

Bridges arch-intelligence's file_id-keyed Layer data into module-name-keyed
lookups (change_planner.ArchitectureModel protocol: get_layer; and
arch_guardrails.ArchModel protocol: get_layers/get_layer_for_module/
get_modules). Per ADR-016, this class must only accept arch_intelligence's
own types plus plain dict[str, str] — never a repo_intelligence type.
"""

from __future__ import annotations

from arch_intelligence.types import ArchitectureModel


class ArchModelAdapter:
    def __init__(self, model: ArchitectureModel, file_to_module: dict[str, str]) -> None:
        self.model = model
        self.file_to_module = file_to_module

        self._layers_sorted = sorted(model.layers, key=lambda layer: layer.number)

        self._module_to_layer_name: dict[str, str] = {}
        for layer in model.layers:
            for file_id in layer.file_ids:
                module = file_to_module.get(file_id)
                if module is not None:
                    self._module_to_layer_name[module] = layer.name

    def get_layer(self, module: str) -> str:
        return self._module_to_layer_name.get(module, "unknown")

    def get_layer_for_module(self, module: str) -> str:
        return self.get_layer(module)

    def get_layers(self) -> list[str]:
        return [layer.name for layer in self._layers_sorted]

    def get_modules(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for module in self._module_to_layer_name:
            if module not in seen:
                seen.add(module)
                ordered.append(module)
        return ordered
