"""Subsystem detection via Louvain clustering."""

import random
from .types import Subsystem


class SubsystemDetector:
    """Detects subsystems using Louvain community detection."""

    def detect_subsystems(self, call_graph: list, symbols: list, files: list) -> list[Subsystem]:
        """
        Detect subsystems via Louvain clustering on call graph.
        Compute coupling_score: inter_calls / (intra_calls + inter_calls).
        """
        if not files or not call_graph:
            return []

        try:
            import networkx as nx
            from networkx.algorithms import community
        except ImportError:
            # Fallback if networkx not available
            return self._simple_clustering(files)

        # Build call graph
        G = nx.DiGraph()
        for f in files:
            G.add_node(f.id)

        symbol_to_file = {s.id: s.file_id for s in symbols}
        for edge in call_graph:
            file_caller = symbol_to_file.get(edge.caller_id)
            file_callee = symbol_to_file.get(edge.callee_id)
            if file_caller and file_callee and file_caller != file_callee:
                G.add_edge(file_caller, file_callee)

        # Louvain clustering with fixed seed
        random.seed(42)
        communities = list(community.louvain_communities(G.to_undirected()))

        # Build subsystems
        subsystems = []
        for i, comm in enumerate(communities):
            file_ids = list(comm)
            name = self._infer_subsystem_name(file_ids, files)

            # Compute coupling score
            intra_calls = 0
            inter_calls = 0
            for edge in call_graph:
                file_caller = symbol_to_file.get(edge.caller_id)
                file_callee = symbol_to_file.get(edge.callee_id)
                if file_caller in file_ids and file_callee in file_ids:
                    intra_calls += 1
                elif (file_caller in file_ids) != (file_callee in file_ids):
                    inter_calls += 1

            coupling = inter_calls / (intra_calls + inter_calls) if (intra_calls + inter_calls) > 0 else 0.0

            subsystem = Subsystem(
                id=f"subsys_{i}",
                name=name,
                file_ids=file_ids,
                coupling_score=min(coupling, 1.0),
            )
            subsystems.append(subsystem)

        return subsystems

    def _infer_subsystem_name(self, file_ids: list, files: list) -> str:
        """Infer subsystem name from common path prefix."""
        if not file_ids:
            return "Subsystem"

        file_map = {f.id: f.rel_path for f in files}
        paths = [file_map.get(fid, "unknown") for fid in file_ids]

        # Find common directory prefix
        if paths:
            parts = [p.split("/") for p in paths]
            common = []
            for i in range(min(len(p) for p in parts)):
                if all(p[i] == parts[0][i] for p in parts):
                    common.append(parts[0][i])
                else:
                    break
            if common:
                return common[-1].replace("_", " ").title()

        return f"Subsystem_{len(file_ids)}"

    def _simple_clustering(self, files: list) -> list[Subsystem]:
        """Fallback clustering by directory."""
        if not files:
            return []

        by_dir = {}
        for f in files:
            parts = f.rel_path.split("/")
            dir_name = parts[0] if len(parts) > 1 else "root"
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(f.id)

        subsystems = []
        for i, (dir_name, file_ids) in enumerate(sorted(by_dir.items())):
            subsystem = Subsystem(
                id=f"subsys_{i}",
                name=dir_name.replace("_", " ").title(),
                file_ids=file_ids,
                coupling_score=0.5,
            )
            subsystems.append(subsystem)

        return subsystems
