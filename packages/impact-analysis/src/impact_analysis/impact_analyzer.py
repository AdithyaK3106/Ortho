"""Impact analyzer: computes blast radius for file/symbol changes."""

from collections import deque
from typing import Optional

from .types import ImpactReport, CallEdge, ImportEdge, Symbol


class ImpactAnalyzer:
    """Analyzes change impact by traversing call and import graphs (stateless)."""

    def analyze(
        self,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        changed_file_id: str,
        symbols: Optional[list[Symbol]] = None,
        depth: int = 3,
    ) -> ImpactReport:
        """
        Analyze impact of changing a file by traversing dependency graphs.

        Args:
            call_graph: List of CallEdge objects representing call relationships
            import_graph: List of ImportEdge objects representing import relationships
            changed_file_id: ID of the file being changed
            symbols: Optional list of Symbol objects for mapping
            depth: Maximum depth to traverse (default 3 hops)

        Returns:
            ImpactReport with direct_dependents, transitive_dependents, risk_score, analysis_confidence
        """
        if symbols is None:
            symbols = []

        # Build symbol index: file_id -> list of symbols
        symbols_by_file = {}
        for sym in symbols:
            if sym.file_id not in symbols_by_file:
                symbols_by_file[sym.file_id] = []
            symbols_by_file[sym.file_id].append(sym)

        # Find direct importers (files that import changed_file)
        direct_importers = set()
        for edge in import_graph:
            if edge.imported_file_id == changed_file_id:
                direct_importers.add(edge.importer_file_id)

        # Find call dependents: symbols in changed_file that are called elsewhere
        symbols_in_changed_file = symbols_by_file.get(changed_file_id, [])
        symbol_ids_in_file = {sym.id for sym in symbols_in_changed_file}

        call_dependents = set()
        for edge in call_graph:
            if edge.callee_id in symbol_ids_in_file:
                # Caller depends on a symbol in changed_file
                caller_sym = next((s for s in symbols if s.id == edge.caller_id), None)
                if caller_sym:
                    call_dependents.add(caller_sym.file_id)

        # Combine direct dependents
        direct_dependents = direct_importers | call_dependents

        # BFS to find transitive dependents up to depth
        transitive_dependents = self._bfs_transitive(
            direct_dependents,
            import_graph,
            depth=depth,
        )

        # Compute risk score based on centrality
        fan_in = len(direct_dependents)
        fan_out_count = sum(1 for edge in import_graph if edge.importer_file_id == changed_file_id)
        num_symbols = max(len(symbols_in_changed_file), 1)
        risk_score = min(1.0, (fan_in + fan_out_count) / (2 * num_symbols))

        # Compute analysis confidence (based on unresolved symbols)
        unresolved = sum(1 for edge in call_graph if edge.confidence < 1.0)
        total = len(call_graph) if call_graph else 0
        analysis_confidence = 1.0 - (unresolved / total if total > 0 else 0.0)

        # Build evidence
        evidence = []
        if fan_in > 0:
            evidence.append(f"{changed_file_id} imported by {fan_in} file(s) (high fan-in)")
        if fan_out_count > 0:
            evidence.append(f"{changed_file_id} imports {fan_out_count} file(s)")
        if call_dependents:
            evidence.append(f"Symbols in {changed_file_id} called from {len(call_dependents)} file(s)")
        if analysis_confidence < 1.0:
            evidence.append(f"Analysis confidence {analysis_confidence:.1%} (unresolved symbols detected)")

        return ImpactReport(
            changed_file_id=changed_file_id,
            direct_dependents=sorted(list(direct_dependents)),
            transitive_dependents=sorted(list(transitive_dependents)),
            risk_score=risk_score,
            analysis_confidence=analysis_confidence,
            blast_radius=len(transitive_dependents),
            evidence=evidence,
        )

    def analyze_symbol(
        self,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        symbols: list[Symbol],
        symbol_id: str,
        depth: int = 3,
    ) -> ImpactReport:
        """
        Analyze impact of changing a specific symbol.

        Args:
            call_graph: List of CallEdge objects
            import_graph: List of ImportEdge objects
            symbols: List of Symbol objects
            symbol_id: ID of the symbol being changed
            depth: Maximum depth to traverse

        Returns:
            ImpactReport for the symbol's dependents
        """
        # Find the file containing this symbol
        sym = next((s for s in symbols if s.id == symbol_id), None)
        if not sym:
            return ImpactReport(
                changed_file_id=symbol_id,
                evidence=["Symbol not found in registry"],
            )

        # Find direct callers of this symbol
        direct_callers = set()
        for edge in call_graph:
            if edge.callee_id == symbol_id:
                caller_sym = next((s for s in symbols if s.id == edge.caller_id), None)
                if caller_sym:
                    direct_callers.add(caller_sym.file_id)

        # BFS from direct callers
        transitive_dependents = self._bfs_transitive(
            direct_callers,
            import_graph,
            depth=depth,
        )

        # Compute risk score
        fan_in = len(direct_callers)
        risk_score = min(1.0, fan_in / 2.0) if fan_in > 0 else 0.0

        # Compute analysis confidence
        unresolved = sum(1 for edge in call_graph if edge.confidence < 1.0)
        total = len(call_graph) if call_graph else 0
        analysis_confidence = 1.0 - (unresolved / total if total > 0 else 0.0)

        # Build evidence
        evidence = []
        if fan_in > 0:
            evidence.append(f"Symbol {symbol_id} called from {fan_in} file(s)")
        if analysis_confidence < 1.0:
            evidence.append(f"Analysis confidence {analysis_confidence:.1%}")

        return ImpactReport(
            changed_file_id=sym.file_id,
            direct_dependents=sorted(list(direct_callers)),
            transitive_dependents=sorted(list(transitive_dependents)),
            risk_score=risk_score,
            analysis_confidence=analysis_confidence,
            blast_radius=len(transitive_dependents),
            evidence=evidence,
        )

    @staticmethod
    def _bfs_transitive(
        start_files: set[str],
        import_graph: list[ImportEdge],
        depth: int,
    ) -> set[str]:
        """BFS traversal to find transitive dependents."""
        visited = set(start_files)
        queue = deque((f, 0) for f in start_files)

        while queue:
            current, current_depth = queue.popleft()

            if current_depth >= depth:
                continue

            # Find files that import current
            for edge in import_graph:
                if edge.imported_file_id == current and edge.importer_file_id not in visited:
                    visited.add(edge.importer_file_id)
                    queue.append((edge.importer_file_id, current_depth + 1))

        # Remove starting files from result (return only reachable dependents)
        return visited - start_files
