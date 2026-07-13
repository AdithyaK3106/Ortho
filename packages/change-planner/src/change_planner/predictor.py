from typing import Any, Protocol

from change_planner.confidence_scorer import ConfidenceScorer
from change_planner.types import EdgeType, ImpactEdge, ImpactPrediction


class CallGraph(Protocol):  # pragma: no cover
    """Protocol for call graph data structure."""

    def find_callers(self, symbol: str, depth: int = 1) -> list[str]:
        """Find functions that call this symbol."""
        ...


class ImportGraph(Protocol):  # pragma: no cover
    """Protocol for import graph data structure."""

    def find_importers(
        self, file_path: str, include_type: bool = False
    ) -> list[tuple[str, str]]:
        """Find modules that import this file."""
        ...


class SymbolRegistry(Protocol):  # pragma: no cover
    """Protocol for symbol registry."""

    def symbols_in_file(self, file_path: str) -> list[str]:
        """Get all symbols defined in a file."""
        ...


class ArchitectureModel(Protocol):  # pragma: no cover
    """Protocol for architecture model."""

    def get_layer(self, module: str) -> str:
        """Get architectural layer for a module."""
        ...


class ChangePredictor:
    def __init__(
        self,
        call_graph: CallGraph,
        import_graph: ImportGraph,
        symbol_registry: SymbolRegistry,
        arch_model: ArchitectureModel,
    ) -> None:
        self.call_graph = call_graph
        self.import_graph = import_graph
        self.symbol_registry = symbol_registry
        self.arch_model = arch_model
        self.scorer = ConfidenceScorer()

    def predict_impact(self, changed_file: str) -> ImpactPrediction:
        """
        Predict impact of changing a file.

        Algorithm:
        1. Extract changed symbols from file
        2. Traverse call graph backward (who calls these symbols)
        3. Traverse import graph (who imports this module)
        4. Score confidence based on edge types + distances
        5. Return ImpactPrediction with evidence
        """
        affected_modules: set[str] = set()
        affected_functions: set[str] = set()
        edges: list[ImpactEdge] = []

        # Step 1: Extract changed symbols from file
        changed_symbols = self._extract_symbols(changed_file)

        # Step 2: Traverse call graph backward
        for symbol in changed_symbols:
            callers, caller_edges = self._find_callers_with_edges(symbol)
            affected_functions.update(callers)
            edges.extend(caller_edges)

        # Step 3: Traverse import graph
        importers, importer_edges = self._find_importers_with_edges(changed_file)
        affected_modules.update(importers)
        edges.extend(importer_edges)

        # Step 4: Score confidence and cascade risk
        confidence = self.scorer.aggregate_confidence(edges)
        cascade_depth = self._compute_max_distance(edges)
        cascade_risk = self.scorer.assess_cascade_risk(
            list(affected_modules), cascade_depth
        )

        # Step 5: Build prediction
        reasoning = self._generate_reasoning(changed_file, edges, affected_modules)

        return ImpactPrediction(
            changed_file=changed_file,
            affected_modules=sorted(affected_modules),
            affected_functions=sorted(affected_functions),
            cascade_risk=cascade_risk,
            confidence=confidence,
            reasoning=reasoning,
            evidence=edges,
        )

    def _extract_symbols(self, file_path: str) -> set[str]:
        """Extract function/class definitions from file"""
        symbols = self.symbol_registry.symbols_in_file(file_path)
        return set(symbols)

    def _find_callers_with_edges(self, symbol: str) -> tuple[set[str], list[ImpactEdge]]:
        """
        Find all functions that (transitively) call this symbol.
        Returns: (set of caller functions, list of edges)
        """
        callers: set[str] = set()
        edges: list[ImpactEdge] = []

        direct_callers = self.call_graph.find_callers(symbol, depth=1)
        for caller in direct_callers:
            callers.add(caller)
            edges.append(
                ImpactEdge(
                    source=caller,
                    target=symbol,
                    edge_type=EdgeType.DIRECT_CALL,
                    distance=1,
                )
            )

        transitive_callers = self.call_graph.find_callers(symbol, depth=10)
        for idx, caller in enumerate(transitive_callers[1:], start=2):
            if caller not in direct_callers:
                callers.add(caller)
                edges.append(
                    ImpactEdge(
                        source=caller,
                        target=symbol,
                        edge_type=EdgeType.TRANSITIVE_CALL,
                        distance=idx,
                    )
                )

        return callers, edges

    def _find_importers_with_edges(self, file_path: str) -> tuple[set[str], list[ImpactEdge]]:
        """
        Find modules importing this file.
        Returns: (set of importer modules, list of edges)
        """
        importers: set[str] = set()
        edges: list[ImpactEdge] = []

        direct_importers = self.import_graph.find_importers(
            file_path, include_type=True
        )
        for importer, import_type in direct_importers:
            importers.add(importer)

            if import_type == "star":
                edge_type = EdgeType.STAR_IMPORT
            elif import_type == "dynamic":
                edge_type = EdgeType.DYNAMIC_IMPORT
            elif import_type == "conditional":
                edge_type = EdgeType.CONDITIONAL_IMPORT
            else:
                edge_type = EdgeType.IMPORT

            edges.append(
                ImpactEdge(
                    source=importer,
                    target=file_path,
                    edge_type=edge_type,
                    distance=1,
                )
            )

        return importers, edges

    def _compute_max_distance(self, edges: list[ImpactEdge]) -> int:
        """Compute maximum distance in evidence edges"""
        if not edges:
            return 0
        return max(edge.distance for edge in edges)

    def _generate_reasoning(
        self, changed_file: str, edges: list[ImpactEdge], affected_modules: set[str]
    ) -> str:
        """Generate human-readable reasoning for prediction"""
        if not edges:
            return f"No impacts detected for changes to {changed_file}."

        impact_lines = [f"Change to {changed_file} impacts:"]

        import_count = sum(
            1
            for e in edges
            if e.edge_type in (EdgeType.IMPORT, EdgeType.STAR_IMPORT, EdgeType.DYNAMIC_IMPORT)
        )
        call_count = sum(
            1
            for e in edges
            if e.edge_type in (EdgeType.DIRECT_CALL, EdgeType.TRANSITIVE_CALL)
        )

        if import_count > 0:
            impact_lines.append(f"  - {import_count} import(s): {affected_modules}")
        if call_count > 0:
            impact_lines.append(f"  - {call_count} call path(s)")

        return "\n".join(impact_lines)
