from typing import Protocol

from arch_guardrails.types import GuardrailViolation


class ArchModel(Protocol):  # pragma: no cover
    """Protocol for architecture model"""

    def get_layers(self) -> list[str]:
        """Get layer hierarchy"""
        ...

    def get_layer_for_module(self, module: str) -> str:
        """Get layer for module"""
        ...

    def get_modules(self) -> list[str]:
        """Get all modules"""
        ...


class DepGraph(Protocol):  # pragma: no cover
    """Protocol for dependency graph"""

    def get_edges(self) -> list[tuple[str, str]]:
        """Get all dependency edges"""
        ...

    def find_cycles(self) -> list[list[str]]:
        """Find all cycles"""
        ...


class CodeMetrics(Protocol):  # pragma: no cover
    """Protocol for code metrics"""

    def get_module_lines(self, module: str) -> int:
        """Get line count"""
        ...

    def get_module_functions(self, module: str) -> int:
        """Get function count"""
        ...


class ArchitectureEnforcer:
    def __init__(
        self,
        arch_model: ArchModel,
        dep_graph: DepGraph,
        metrics: CodeMetrics,
    ) -> None:
        self.arch_model = arch_model
        self.dep_graph = dep_graph
        self.metrics = metrics

    def check_violations(self) -> list[GuardrailViolation]:
        """
        Check all architectural guardrails.
        Returns violations sorted by severity.
        """
        violations: list[GuardrailViolation] = []

        # layer_boundaries: re-enabled 2026-07-16 after LayerDetector was
        # redesigned to require real evidence (a module actually importing a
        # known persistence/ORM library or a known web/API/CLI framework)
        # instead of import-graph topological depth, which caused a 100%
        # false-positive rate on the 9-repo audit (see
        # docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md). Modules with no
        # such evidence are now excluded from layer assignment entirely
        # (get_layer_for_module returns "unknown", which this method already
        # skips) rather than defaulted into layer 0.
        violations.extend(self._check_layer_boundaries())

        # Check dependency direction (acyclic)
        violations.extend(self._check_dependency_direction())

        # Check module sizing
        violations.extend(self._check_module_sizing())

        # Sort by severity
        violations.sort(key=lambda v: (
            {"error": 0, "warning": 1}[v.severity],
            v.location
        ))

        return violations

    def _check_layer_boundaries(self) -> list[GuardrailViolation]:
        """Enforce layer hierarchy (dependencies flow downward only)"""
        violations: list[GuardrailViolation] = []
        layers = self.arch_model.get_layers()
        layer_order = {layer: idx for idx, layer in enumerate(layers)}

        for source, target in self.dep_graph.get_edges():
            source_layer = self.arch_model.get_layer_for_module(source)
            target_layer = self.arch_model.get_layer_for_module(target)

            if source_layer != "unknown" and target_layer != "unknown":
                src_idx = layer_order.get(source_layer, -1)
                tgt_idx = layer_order.get(target_layer, -1)
                # Violation: higher layer imports lower layer (upward dependency)
                if src_idx > tgt_idx:
                    violations.append(GuardrailViolation(
                        rule_id="layer_boundaries",
                        severity="error",
                        location=f"{source} → {target}",
                        message=f"{source_layer} cannot import {target_layer}",
                        suggested_fix="Invert dependency or use abstraction",
                        evidence=[
                            f"{source} is classified {source_layer} (layer index {src_idx})",
                            f"{target} is classified {target_layer} (layer index {tgt_idx})",
                            f"declared layer order: {' < '.join(layers)}",
                            f"real import edge {source} → {target} found in the dependency graph",
                        ],
                    ))

        return violations

    def _check_dependency_direction(self) -> list[GuardrailViolation]:
        """Enforce acyclic dependencies"""
        violations: list[GuardrailViolation] = []
        cycles = self.dep_graph.find_cycles()

        for cycle in cycles:
            # cycle is a closed loop: [a, b, c, a]. Each consecutive pair is a
            # real edge from the dependency graph, not a fabricated claim.
            # Capped at 10 edges: a large SCC (celery's real 41-module cycle)
            # would otherwise turn "evidence" into an unreadable wall of text.
            edges_in_cycle = [f"{cycle[i]} → {cycle[i + 1]}" for i in range(len(cycle) - 1)]
            shown_edges = edges_in_cycle[:10]
            evidence = [f"{len(cycle) - 1}-module cycle: {len(set(cycle))} distinct modules"]
            evidence.extend(f"real import edge: {edge}" for edge in shown_edges)
            if len(edges_in_cycle) > len(shown_edges):
                evidence.append(f"...and {len(edges_in_cycle) - len(shown_edges)} more edges in this cycle")
            violations.append(GuardrailViolation(
                rule_id="dependency_direction",
                severity="error",
                location=" → ".join(cycle),
                message=f"Circular dependency: {' → '.join(cycle)}",
                suggested_fix="Break cycle by extracting abstraction",
                evidence=evidence,
            ))

        return violations

    def _check_module_sizing(self) -> list[GuardrailViolation]:
        """Enforce module size limits"""
        violations: list[GuardrailViolation] = []
        max_lines = 500
        max_functions = 50

        for module in self.arch_model.get_modules():
            lines = self.metrics.get_module_lines(module)
            functions = self.metrics.get_module_functions(module)

            if lines > max_lines:
                violations.append(GuardrailViolation(
                    rule_id="module_sizing",
                    severity="warning",
                    location=module,
                    message=f"Module exceeds {max_lines} lines ({lines})",
                    suggested_fix="Split into focused modules",
                    evidence=[
                        f"{module} measured at {lines} lines (limit: {max_lines})",
                        f"{lines - max_lines} lines over the limit",
                    ],
                ))

            if functions > max_functions:
                violations.append(GuardrailViolation(
                    rule_id="module_sizing",
                    severity="warning",
                    location=module,
                    message=f"Module exceeds {max_functions} functions ({functions})",
                    suggested_fix="Group related functions into new modules",
                    evidence=[
                        f"{module} measured at {functions} functions (limit: {max_functions})",
                        f"{functions - max_functions} functions over the limit",
                    ],
                ))

        return violations
