"""Dependency health analyzer: detects coupling patterns and circular dependencies."""

from typing import Optional

from .types import DependencyHealthReport, CallEdge, ImportEdge


class DependencyHealthAnalyzer:
    """Analyzes dependency health and identifies problematic patterns (stateless)."""

    # Phase 1 default thresholds (configurable in future)
    DEFAULT_THRESHOLDS = {
        "high_fan_in": 10,
        "high_fan_out": 15,
        "hub_fan_in": 8,
        "hub_fan_out": 8,
    }

    def analyze_module(
        self,
        file_id: str,
        import_graph: list[ImportEdge],
        architecture_model: Optional[dict] = None,
    ) -> DependencyHealthReport:
        """
        Analyze health of a single module (stateless).

        Args:
            file_id: ID of the file to analyze
            call_graph: List of CallEdge objects
            import_graph: List of ImportEdge objects
            architecture_model: Optional architecture model for context

        Returns:
            DependencyHealthReport with patterns, recommendations, and evidence
        """
        # Count fan-in and fan-out
        fan_in = sum(1 for edge in import_graph if edge.imported_file_id == file_id and not edge.is_external)
        fan_out = sum(1 for edge in import_graph if edge.importer_file_id == file_id)

        # Detect patterns
        high_fan_in = fan_in > self.DEFAULT_THRESHOLDS["high_fan_in"]
        high_fan_out = fan_out > self.DEFAULT_THRESHOLDS["high_fan_out"]
        is_hub = (
            fan_in > self.DEFAULT_THRESHOLDS["hub_fan_in"]
            and fan_out > self.DEFAULT_THRESHOLDS["hub_fan_out"]
        )

        # Find cycles involving this file
        cycles = self._find_cycles_for_file(file_id, import_graph)

        # Generate recommendations
        recommendations = []
        if high_fan_in:
            recommendations.append("This is a core module; test thoroughly and consider as potential bottleneck")
        if high_fan_out:
            recommendations.append("High dependencies; consider layering or breaking into smaller modules")
        if is_hub:
            recommendations.append("Hub module detected; extract into separate layer or refactor into focused modules")
        if cycles:
            recommendations.append("Circular dependency detected; break cycle with interface/abstraction")

        # Build evidence
        evidence = []
        if high_fan_in:
            evidence.append(f"High fan-in: {fan_in} files import this module (threshold: {self.DEFAULT_THRESHOLDS['high_fan_in']})")
        if high_fan_out:
            evidence.append(f"High fan-out: {fan_out} dependencies (threshold: {self.DEFAULT_THRESHOLDS['high_fan_out']})")
        if cycles:
            for cycle in cycles:
                evidence.append(f"Cycle detected: {' → '.join(cycle)}")

        return DependencyHealthReport(
            module_id=file_id,
            fan_in=fan_in,
            fan_out=fan_out,
            high_fan_in=high_fan_in,
            high_fan_out=high_fan_out,
            is_hub=is_hub,
            cycles_involved=cycles,
            recommendations=recommendations,
            evidence=evidence,
        )

    def analyze_all_modules(
        self,
        import_graph: list[ImportEdge],
        architecture_model: Optional[dict] = None,
    ) -> list[DependencyHealthReport]:
        """
        Full repository health report (stateless).

        Args:
            import_graph: List of ImportEdge objects
            architecture_model: Optional architecture model for context

        Returns:
            List of DependencyHealthReport for all modules
        """
        # Collect unique file IDs
        file_ids = set()
        for edge in import_graph:
            file_ids.add(edge.importer_file_id)
            if edge.imported_file_id and not edge.is_external:
                file_ids.add(edge.imported_file_id)

        # Analyze each module
        reports = []
        for file_id in file_ids:
            report = self.analyze_module(file_id, import_graph, architecture_model)
            reports.append(report)

        # Sort by is_hub, then high_fan_in, for better visibility
        return sorted(
            reports,
            key=lambda r: (not r.is_hub, not r.high_fan_in, -r.fan_in),
        )

    def find_cycles(
        self,
        import_graph: list[ImportEdge],
    ) -> list[list[str]]:
        """
        Detect all circular dependency chains (stateless).

        Args:
            import_graph: List of ImportEdge objects

        Returns:
            List of cycle chains: [[A, B, C, A], ...]
        """
        # Collect unique file IDs
        file_ids = set()
        for edge in import_graph:
            file_ids.add(edge.importer_file_id)
            if edge.imported_file_id and not edge.is_external:
                file_ids.add(edge.imported_file_id)

        # Build adjacency list
        graph = {file_id: [] for file_id in file_ids}
        for edge in import_graph:
            if edge.imported_file_id and not edge.is_external:
                graph[edge.importer_file_id].append(edge.imported_file_id)

        # DFS-based cycle detection
        all_cycles = []
        visited = set()
        rec_stack = set()

        def dfs_visit(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs_visit(neighbor, path)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    all_cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        # Run DFS from each unvisited node
        for file_id in file_ids:
            if file_id not in visited:
                dfs_visit(file_id, [])

        return all_cycles

    @staticmethod
    def _find_cycles_for_file(
        file_id: str,
        import_graph: list[ImportEdge],
    ) -> list[list[str]]:
        """Find cycles that include a specific file."""
        # Build adjacency list
        graph = {}
        file_ids = set()
        for edge in import_graph:
            file_ids.add(edge.importer_file_id)
            if edge.imported_file_id and not edge.is_external:
                file_ids.add(edge.imported_file_id)

        for fid in file_ids:
            graph[fid] = []

        for edge in import_graph:
            if edge.imported_file_id and not edge.is_external:
                graph[edge.importer_file_id].append(edge.imported_file_id)

        # Find cycles involving this file using BFS
        cycles = []
        visited = set()
        queue = [(file_id, [file_id])]

        while queue:
            current, path = queue.pop(0)

            for neighbor in graph.get(current, []):
                if neighbor == file_id and len(path) > 1:
                    # Found a cycle back to file_id
                    cycles.append(path + [file_id])
                elif neighbor not in path and neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

            visited.add(current)

        return cycles
