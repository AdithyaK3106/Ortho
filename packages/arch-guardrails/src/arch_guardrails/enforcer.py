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

        # layer_boundaries is disabled pending a redesign of layer detection.
        # A false-positive audit against 9 real repos (2026-07-16, see
        # docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md) found this rule
        # fired 177 times across 5 repos with a 100% false-positive rate:
        # the current LayerDetector assigns "layer 0" to any module with no
        # internal imports (a mechanical fact about import topology) and a
        # semantic name via keyword match, then flags every importer of that
        # module as a boundary violation -- but "imports a leaf/config/utils
        # module" is one of the most ordinary patterns in software, not
        # evidence of an architecture problem. This method (_check_layer_
        # boundaries) itself is correct given accurate layer data -- see
        # test_enforcer.py's TestLayerBoundaries, which still exercises it
        # directly against hand-labeled layers -- the defect is entirely in
        # what LayerDetector currently reports as "the layers." Re-enable
        # once layer assignment has real evidence behind it (e.g. persistence/
        # IO signature, not just topological depth), not before.
        #
        # violations.extend(self._check_layer_boundaries())

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
                        suggested_fix="Invert dependency or use abstraction"
                    ))

        return violations

    def _check_dependency_direction(self) -> list[GuardrailViolation]:
        """Enforce acyclic dependencies"""
        violations: list[GuardrailViolation] = []
        cycles = self.dep_graph.find_cycles()

        for cycle in cycles:
            violations.append(GuardrailViolation(
                rule_id="dependency_direction",
                severity="error",
                location=" → ".join(cycle),
                message=f"Circular dependency: {' → '.join(cycle)}",
                suggested_fix="Break cycle by extracting abstraction"
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
                    suggested_fix="Split into focused modules"
                ))

            if functions > max_functions:
                violations.append(GuardrailViolation(
                    rule_id="module_sizing",
                    severity="warning",
                    location=module,
                    message=f"Module exceeds {max_functions} functions ({functions})",
                    suggested_fix="Group related functions into new modules"
                ))

        return violations
