"""Subsystem detection via clustering."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Set

import networkx as nx
from networkx.algorithms import community

# Add shared storage to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))

from database import OrthoDatabase

try:
    from .graph_utils import FileGraph
except (ImportError, ValueError):
    from graph_utils import FileGraph


@dataclass
class Subsystem:
    """Detected subsystem (cluster of related modules)."""

    id: str
    name: str
    file_ids: list[str]
    layer_id: str | None
    coupling_score: float


class SubsystemDetector:
    """Cluster related modules into subsystems."""

    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
        self.file_graph = FileGraph(db, repo_id)

    def detect_subsystems(self) -> list[Subsystem]:
        """
        Detect subsystems via Louvain community detection.
        Returns Subsystem objects sorted by coupling score (descending).
        """
        graph = self.file_graph.build_from_imports()

        if len(graph) < 3:
            # Too small, treat as single subsystem
            all_files = list(graph.nodes())
            return [
                Subsystem(
                    id="subsystem_0",
                    name="main",
                    file_ids=all_files,
                    layer_id=None,
                    coupling_score=0.0,
                )
            ]

        # Community detection
        try:
            communities_list = list(community.greedy_modularity_communities(graph))
        except (nx.NetworkXError, ValueError):
            # Fallback: treat as single subsystem
            all_files = list(graph.nodes())
            return [
                Subsystem(
                    id="subsystem_0",
                    name="main",
                    file_ids=all_files,
                    layer_id=None,
                    coupling_score=self._compute_coupling_score(set(all_files), graph),
                )
            ]

        subsystems = []
        for i, community_files in enumerate(communities_list):
            community_set = set(community_files)
            name = self._suggest_subsystem_name(list(community_set))
            coupling = self._compute_coupling_score(community_set, graph)

            subsystems.append(
                Subsystem(
                    id=f"subsystem_{i}",
                    name=name,
                    file_ids=list(community_set),
                    layer_id=None,
                    coupling_score=coupling,
                )
            )

        # Sort by coupling (descending)
        subsystems.sort(key=lambda x: -x.coupling_score)

        return subsystems

    def _compute_coupling_score(self, subsystem_files: Set[str], graph: nx.DiGraph) -> float:
        """
        Coupling = internal edges / max possible edges.
        0.0 = isolated; 1.0 = fully connected.
        """
        if len(subsystem_files) < 2:
            return 0.0

        # Count internal edges
        internal_edges = 0
        for u, v in graph.edges():
            if u in subsystem_files and v in subsystem_files:
                internal_edges += 1

        # Max possible edges (complete directed graph)
        n = len(subsystem_files)
        max_edges = n * (n - 1)

        if max_edges == 0:
            return 0.0

        return internal_edges / max_edges

    def _suggest_subsystem_name(self, file_ids: list[str]) -> str:
        """
        Auto-name subsystem from file paths or keywords.
        Falls back to auto-numbering.
        """
        if not file_ids:
            return "unknown"

        # Get file paths
        conn = self.db.connection()
        paths = conn.execute(
            "SELECT rel_path FROM files WHERE id IN ({})".format(
                ",".join("?" * len(file_ids))
            ),
            file_ids,
        ).fetchall()
        conn.close()

        if not paths:
            return "unknown"

        # Extract common directory prefix
        rel_paths = [p[0] for p in paths]
        common_prefix = self._find_common_prefix(rel_paths)

        if common_prefix and common_prefix != ".":
            # Use directory name
            parts = common_prefix.split("/")
            if parts:
                return parts[0].lower()

        # Fallback: extract keywords from file names
        keywords = []
        for path in rel_paths:
            parts = path.split("/")
            for part in parts:
                keywords.append(part.replace(".py", "").replace("_", " "))

        # Find most common keyword
        from collections import Counter
        common = Counter(keywords).most_common(1)
        if common:
            return common[0][0].lower()

        return "unknown"

    def _find_common_prefix(self, paths: list[str]) -> str:
        """Find common directory prefix of paths."""
        if not paths:
            return ""

        # Split paths into parts
        split_paths = [p.split("/") for p in paths]

        # Find common prefix length
        min_len = min(len(parts) for parts in split_paths)
        common_parts = []

        for i in range(min_len):
            part = split_paths[0][i]
            if all(parts[i] == part for parts in split_paths):
                common_parts.append(part)
            else:
                break

        return "/".join(common_parts)
