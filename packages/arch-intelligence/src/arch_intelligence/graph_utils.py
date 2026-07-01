"""Graph utilities for architecture analysis."""

import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple

import networkx as nx

# Add shared storage to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))

from storage import OrthoDatabase


class FileGraph:
    """Build and analyze file dependency graphs."""

    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
        self._graph = None
        self._reverse_graph = None

    def build_from_imports(self) -> nx.DiGraph:
        """Build file dependency graph from import edges."""
        if self._graph is not None:
            return self._graph

        g = nx.DiGraph()
        conn = self.db.connection()

        # Add file nodes
        files = conn.execute(
            "SELECT id FROM files WHERE repo_id = ?", (self.repo_id,)
        ).fetchall()
        for (file_id,) in files:
            g.add_node(file_id)

        # Add import edges (importer → imported)
        edges = conn.execute(
            """
            SELECT importer_file_id, imported_file_id
            FROM import_edges
            WHERE imported_file_id IS NOT NULL
              AND importer_file_id IN (SELECT id FROM files WHERE repo_id = ?)
            """,
            (self.repo_id,),
        ).fetchall()

        for importer, imported in edges:
            if g.has_node(imported):
                g.add_edge(importer, imported)

        conn.close()
        self._graph = g
        return g

    def build_reverse_graph(self) -> nx.DiGraph:
        """Get reverse dependency graph (what depends on X)."""
        if self._reverse_graph is not None:
            return self._reverse_graph

        g = self.build_from_imports()
        self._reverse_graph = g.reverse()
        return self._reverse_graph

    def topological_levels(self) -> Dict[str, int]:
        """
        Compute topological level for each file in the dependency DAG.
        Level = 1 + max(level of all files this file depends on).
        Files with no dependencies (sources) are at level 0.
        Files that depend on level 0 are at level 1, etc.

        Graph edges: importer → imported (u imports v)
        So: level(u) = 1 + max(level(v) for v in g.successors(u))
        """
        g = self.build_from_imports()
        levels = {}

        # Find nodes with no incoming edges (sources = level 0)
        # In import graph, in_degree = 0 means nothing imports from this file
        # We want nodes with NO dependencies (out_degree = 0 in reverse graph)
        # Actually: files with out_degree 0 have NO successors in import graph
        # = they don't depend on anything = they should be level 0
        for node in g.nodes():
            if g.out_degree(node) == 0:
                levels[node] = 0

        # Iteratively compute levels for nodes with dependencies
        # For each node, level = 1 + max(level of dependencies)
        # Dependencies = successors in the import graph
        changed = True
        while changed:
            changed = False
            for node in g.nodes():
                if node in levels:
                    continue

                # Get files this node depends on (imports from)
                deps = list(g.successors(node))

                # If all dependencies have been assigned levels
                if all(dep in levels for dep in deps):
                    levels[node] = 1 + max((levels[dep] for dep in deps), default=-1)
                    changed = True

        # Handle any remaining nodes (shouldn't happen if graph is acyclic)
        for node in g.nodes():
            if node not in levels:
                levels[node] = 0

        return levels

    def detect_cycles(self) -> List[List[str]]:
        """Find all cycles in the dependency graph."""
        g = self.build_from_imports()
        return list(nx.simple_cycles(g))

    def transitive_dependents(self, file_id: str, depth: int = 3) -> Set[str]:
        """Find all files that transitively depend on file_id (within depth hops)."""
        g = self.build_reverse_graph()

        visited = set()
        queue = deque([(file_id, 0)])

        while queue:
            node, d = queue.popleft()
            if d > depth or node in visited:
                continue

            visited.add(node)
            for successor in g.successors(node):
                if successor not in visited:
                    queue.append((successor, d + 1))

        visited.discard(file_id)
        return visited

    def direct_dependents(self, file_id: str) -> Set[str]:
        """Files that directly import file_id."""
        g = self.build_reverse_graph()
        return set(g.successors(file_id))

    def centrality_score(self, file_id: str) -> float:
        """
        Compute centrality score for a file (0.0 - 1.0).
        Based on in-degree + betweenness centrality.
        """
        g = self.build_from_imports()

        # In-degree (fan-in): how many files import this one
        in_degree = g.in_degree(file_id)
        max_in_degree = len(g.nodes()) - 1
        degree_score: float = in_degree / max_in_degree if max_in_degree > 0 else 0.0

        # Betweenness centrality: how often on shortest paths
        try:
            betweenness = nx.betweenness_centrality(g)
            centrality_score: float = betweenness.get(file_id, 0.0)
        except (nx.NetworkXError, ZeroDivisionError):
            centrality_score = 0.0

        # Combined score (weighted)
        return 0.6 * degree_score + 0.4 * centrality_score


class CallGraph:
    """Build and analyze call dependency graphs."""

    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
        self._graph = None

    def build_from_calls(self) -> nx.DiGraph:
        """Build call graph from call edges."""
        if self._graph is not None:
            return self._graph

        g = nx.DiGraph()
        conn = self.db.connection()

        # Get all symbols (nodes)
        symbols = conn.execute(
            "SELECT id FROM symbols WHERE repo_id = ?", (self.repo_id,)
        ).fetchall()
        for (symbol_id,) in symbols:
            g.add_node(symbol_id)

        # Add call edges
        edges = conn.execute(
            """
            SELECT caller_id, callee_id
            FROM call_edges
            WHERE caller_id IN (SELECT id FROM symbols WHERE repo_id = ?)
            """,
            (self.repo_id,),
        ).fetchall()

        for caller, callee in edges:
            if g.has_node(callee):
                g.add_edge(caller, callee)

        conn.close()
        self._graph = g
        return g

    def detect_cycles(self) -> List[List[str]]:
        """Find cycles in call graph."""
        g = self.build_from_calls()
        return list(nx.simple_cycles(g))

    def transitive_callees(self, symbol_id: str, depth: int = 3) -> Set[str]:
        """Symbols called (transitively) by symbol_id."""
        g = self.build_from_calls()

        visited = set()
        queue = deque([(symbol_id, 0)])

        while queue:
            node, d = queue.popleft()
            if d > depth or node in visited:
                continue

            visited.add(node)
            for successor in g.successors(node):
                if successor not in visited:
                    queue.append((successor, d + 1))

        visited.discard(symbol_id)
        return visited


class MetricsCalculator:
    """Compute architecture metrics."""

    def __init__(self, file_graph: FileGraph, call_graph: CallGraph):
        self.file_graph = file_graph
        self.call_graph = call_graph

    def layering_score(self) -> float:
        """
        Score how well the repo follows layered architecture.
        High if: mostly upward dependencies (clean layers).
        Low if: many cross-layer or downward deps.

        Topological levels: level 0 = no deps (deepest), level N = depends on level N-1 (highest)
        Upward edge: u (higher level) imports v (lower level) = level_u > level_v
        Downward edge: u (lower level) imports v (higher level) = level_u < level_v

        Returns 0.0 (flat) to 1.0 (perfect layers).
        """
        g = self.file_graph.build_from_imports()

        if len(g) < 2:
            return 0.5

        levels = self.file_graph.topological_levels()

        # Count upward (good) vs downward/cross-layer (bad) edges
        upward_edges = 0
        downward_edges = 0

        for u, v in g.edges():
            level_u = levels.get(u, 0)
            level_v = levels.get(v, 0)

            # CRITICAL FIX: Upward means u is at higher level and imports v at lower level
            if level_u > level_v:
                upward_edges += 1
            else:
                downward_edges += 1

        total = upward_edges + downward_edges
        if total == 0:
            return 0.5

        # Score: high if mostly upward (correct dependency direction)
        return upward_edges / total

    def cohesion_score(self) -> float:
        """
        Score internal coupling within modules.
        High if: dense internal connections.
        Low if: sparse module coupling.

        Returns 0.0 (isolated) to 1.0 (highly coupled).
        """
        g = self.file_graph.build_from_imports()

        if len(g) < 2:
            return 0.5

        # Density = actual edges / possible edges
        density = nx.density(g)
        return min(1.0, density * 2)  # Scale to 0-1

    def modularity_score(self) -> float:
        """
        Score module independence.
        High if: distinct independent modules.
        Low if: highly interconnected.

        Returns 0.0 (flat) to 1.0 (perfect subsystems).
        """
        g = self.file_graph.build_from_imports()

        if len(g) < 3:
            return 0.5

        # Use modularity metric (requires community detection)
        try:
            from networkx.algorithms import community
            communities = list(community.greedy_modularity_communities(g))

            if len(communities) < 2:
                return 0.3

            # Calculate modularity
            modularity_value: float = community.modularity(g, communities)
            # Map [-0.5, 1.0] to [0.0, 1.0]
            return (modularity_value + 0.5) / 1.5
        except (nx.NetworkXError, ValueError):
            return 0.5
