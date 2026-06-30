"""Layer detection from import patterns."""

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import networkx as nx

# Add shared storage to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))

from database import OrthoDatabase

try:
    from .graph_utils import FileGraph
except (ImportError, ValueError):
    from graph_utils import FileGraph


@dataclass
class Layer:
    """Detected architectural layer."""

    id: str
    name: str
    file_ids: list[str]
    depends_on: list[str]
    confidence: float


class LayerDetector:
    """Identify logical layers from import/call patterns."""

    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
        self.file_graph = FileGraph(db, repo_id)

    def detect_layers(self) -> list[Layer]:
        """
        Extract layers using topological sorting.
        Returns layers ordered top (highest level) to bottom.
        """
        levels = self.file_graph.topological_levels()

        # Cluster files by level
        levels_by_layer = defaultdict(list)
        for file_id, level in levels.items():
            levels_by_layer[level].append(file_id)

        # Assign semantic names
        names = self._assign_semantic_names(sorted(levels_by_layer.items()))

        # Build Layer objects (ordered by level, descending)
        layers = []
        for level in sorted(levels_by_layer.keys(), reverse=True):
            file_ids = levels_by_layer[level]
            layer = Layer(
                id=f"layer_{level}",
                name=names.get(level, f"level_{level}"),
                file_ids=file_ids,
                depends_on=[],  # Computed below
                confidence=self._compute_layer_confidence(file_ids, level),
            )
            layers.append(layer)

        # Compute inter-layer dependencies
        graph = self.file_graph.build_from_imports()
        layer_by_file = {}
        for layer in layers:
            for file_id in layer.file_ids:
                layer_by_file[file_id] = layer.id

        for layer in layers:
            for file_id in layer.file_ids:
                for dep_file_id in graph.predecessors(file_id):
                    # Which layer does dependency belong to?
                    dep_layer_id = layer_by_file.get(dep_file_id)
                    if dep_layer_id and dep_layer_id != layer.id:
                        if dep_layer_id not in layer.depends_on:
                            layer.depends_on.append(dep_layer_id)

        return layers

    def detect_layer_violations(self) -> list[str]:
        """Find cross-layer dependencies (violations of clean architecture)."""
        layers = self.detect_layers()
        graph = self.file_graph.build_from_imports()

        # Map file to layer
        layer_by_file = {}
        for layer in layers:
            for file_id in layer.file_ids:
                layer_by_file[file_id] = layer.name

        violations = []

        # Check each edge for violations
        for u, v in graph.edges():
            layer_u = layer_by_file.get(u)
            layer_v = layer_by_file.get(v)

            if layer_u and layer_v and layer_u != layer_v:
                # Check if this violates layer hierarchy
                violations.append(f"{layer_u} imports {layer_v} (cross-layer)")

        return violations

    def _assign_semantic_names(self, levels_with_files: list[tuple[int, list[str]]]) -> dict[int, str]:
        """
        Map topological level to semantic layer name.
        Highest level (most general) → presentation/api.
        Middle → business/domain.
        Lowest (most specific) → data/storage.

        CRITICAL: Levels are sorted ascending, so:
        - First level (sorted[0]) = lowest topological level = most independent = data layer
        - Last level (sorted[-1]) = highest topological level = most dependent = presentation layer
        """
        names = {}
        num_levels = len(levels_with_files)

        for i, (level, files) in enumerate(levels_with_files):
            # REVERSE position: higher index = higher in dependency graph = presentation
            position_from_top = num_levels - 1 - i

            # Heuristic: infer from file paths first
            inferred = self._infer_layer_name(files)
            if inferred:
                names[level] = inferred
            else:
                # Fallback: assign by reverse position (highest imports from lowest)
                if position_from_top == num_levels - 1:
                    # Top tier (highest dependency, imports from all)
                    names[level] = "presentation"
                elif position_from_top == 0:
                    # Bottom tier (lowest dependency, imports from none)
                    names[level] = "data"
                else:
                    # Middle tier(s)
                    names[level] = "business"

        return names

    def _infer_layer_name(self, file_ids: list[str]) -> str | None:
        """
        Infer layer name from file paths.
        Examples: handlers/, views/ → presentation; services/ → business; models/, db/ → data.
        """
        conn = self.db.connection()
        paths = conn.execute(
            "SELECT rel_path FROM files WHERE id IN ({})".format(
                ",".join("?" * len(file_ids))
            ),
            file_ids,
        ).fetchall()
        conn.close()

        path_parts = []
        for (path,) in paths:
            parts = path.split("/")
            if parts:
                path_parts.append(parts[0].lower())

        if not path_parts:
            return None

        # Check for common patterns
        path_str = " ".join(path_parts)

        if any(p in path_str for p in ["handler", "view", "api", "web", "ui", "route"]):
            return "presentation"
        elif any(p in path_str for p in ["service", "business", "logic", "domain"]):
            return "business"
        elif any(p in path_str for p in ["model", "db", "data", "repository", "storage"]):
            return "data"
        elif any(p in path_str for p in ["util", "config", "infrastructure"]):
            return "infrastructure"

        return None

    def _compute_layer_confidence(self, file_ids: list[str], level: int) -> float:
        """
        Compute confidence in layer assignment.
        High if: clear imports from level above; low if: mixed patterns.
        """
        if not file_ids:
            return 0.5

        graph = self.file_graph.build_from_imports()

        # Check how many files in this layer follow the layer pattern
        conforming = 0
        for file_id in file_ids:
            # This file should only depend on files at higher levels
            deps_at_same_level = 0
            for dep in graph.predecessors(file_id):
                if dep in file_ids:
                    deps_at_same_level += 1

            if deps_at_same_level == 0:
                conforming += 1

        return conforming / len(file_ids) if file_ids else 0.5
