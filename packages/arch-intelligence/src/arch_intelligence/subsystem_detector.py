"""Subsystem detection via multi-signal package-graph clustering.

Previous approach ran Louvain directly on the file-level call graph. Real
repositories drop most dynamic calls as unresolved (ADR-011 "never guess"),
which left the graph so sparse that almost every file became its own
singleton community (978 subsystems for FastAPI, 1733 for LangChain).

New approach — cluster *packages*, not files, over a composite evidence
graph:

  1. Every file belongs to its package (directory). Packages are the nodes.
  2. Edge weights combine three independent, generic signals:
       - internal import edges between packages   (weight 1.0 each)
       - call edges between packages              (weight 0.5 each)
       - parent/child package hierarchy affinity  (weight 0.25)
  3. Louvain (seed=42) clusters the weighted package graph; each community
     of packages is one subsystem, containing all files of its packages.

Files therefore always land in a logical component (their package), and
sparse call data enriches rather than defines the graph. Deterministic:
fixed seed, sorted iteration, stable IDs. No repository-specific rules.
"""

from .types import Subsystem


# Signal weights: imports are the strongest structural evidence, calls are
# supporting (sparse after unresolved-drop), hierarchy is weak glue that
# keeps leaf packages attached to their parent instead of orphaned.
W_IMPORT = 1.0
W_CALL = 0.5
W_HIERARCHY = 0.25


class SubsystemDetector:
    """Detects subsystems by clustering a multi-signal package graph."""

    def detect_subsystems(
        self,
        call_graph: list,
        symbols: list,
        files: list,
        import_graph: list = None,
    ) -> list[Subsystem]:
        """
        Detect subsystems. `import_graph` is optional for backward
        compatibility with pre-existing callers; passing it substantially
        improves clustering on repos with sparse call graphs.
        """
        if not files:
            return []

        pkg_of_file, files_of_pkg = self._package_map(files)

        edge_weights = self._package_edges(
            call_graph, symbols, files, import_graph or [], pkg_of_file
        )

        communities = self._cluster(sorted(files_of_pkg), edge_weights)

        # Build subsystems (deterministic order: by smallest member package)
        communities = sorted(communities, key=lambda c: sorted(c)[0])
        subsystems = []
        for i, pkgs in enumerate(communities):
            file_ids = sorted(
                fid for pkg in pkgs for fid in files_of_pkg[pkg]
            )
            name = self._infer_name(sorted(pkgs), files_of_pkg)
            coupling = self._coupling(pkgs, edge_weights)
            subsystems.append(
                Subsystem(
                    id=f"subsys_{i}",
                    name=name,
                    file_ids=file_ids,
                    coupling_score=coupling,
                )
            )
        return subsystems

    # -- Graph construction --------------------------------------------------

    @staticmethod
    def _package_map(files):
        """Map each file to its package (directory path; '.' for root)."""
        pkg_of_file = {}
        files_of_pkg = {}
        for f in files:
            rel = f.rel_path.replace("\\", "/")
            pkg = rel.rsplit("/", 1)[0] if "/" in rel else "."
            pkg_of_file[f.id] = pkg
            files_of_pkg.setdefault(pkg, []).append(f.id)
        return pkg_of_file, files_of_pkg

    @staticmethod
    def _package_edges(call_graph, symbols, files, import_graph, pkg_of_file):
        """Composite weighted edges between packages from all signals."""
        weights = {}

        def add(a, b, w):
            if a == b:
                return
            key = (a, b) if a < b else (b, a)
            weights[key] = weights.get(key, 0.0) + w

        # Signal 1: internal imports (file -> file, mapped to packages)
        for e in import_graph:
            imported = getattr(e, "imported_file_id", None)
            if imported and imported in pkg_of_file and e.importer_file_id in pkg_of_file:
                add(pkg_of_file[e.importer_file_id], pkg_of_file[imported], W_IMPORT)

        # Signal 2: call edges (symbol -> symbol, mapped via symbols to files)
        symbol_to_file = {s.id: s.file_id for s in symbols}
        for e in call_graph:
            fa = symbol_to_file.get(e.caller_id, e.caller_id)
            fb = symbol_to_file.get(e.callee_id, e.callee_id)
            if fa in pkg_of_file and fb in pkg_of_file:
                add(pkg_of_file[fa], pkg_of_file[fb], W_CALL)

        # Signal 3: namespace hierarchy (package -> nearest existing ancestor)
        pkgs = set(pkg_of_file.values())
        for pkg in sorted(pkgs):
            if pkg == ".":
                continue
            parent = pkg
            while "/" in parent:
                parent = parent.rsplit("/", 1)[0]
                if parent in pkgs:
                    add(pkg, parent, W_HIERARCHY)
                    break

        return weights

    # -- Clustering -----------------------------------------------------------

    @staticmethod
    def _cluster(packages, edge_weights):
        """Louvain communities over the weighted package graph (seed=42)."""
        try:
            import networkx as nx
            from networkx.algorithms import community
        except ImportError:
            # Fallback: group packages by top-level directory
            groups = {}
            for pkg in packages:
                top = pkg.split("/", 1)[0]
                groups.setdefault(top, set()).add(pkg)
            return [groups[k] for k in sorted(groups)]

        G = nx.Graph()
        G.add_nodes_from(packages)
        for (a, b), w in sorted(edge_weights.items()):
            G.add_edge(a, b, weight=w)

        return [
            set(c)
            for c in community.louvain_communities(G, weight="weight", seed=42)
        ]

    # -- Metrics / naming ------------------------------------------------------

    @staticmethod
    def _coupling(pkgs, edge_weights):
        """inter-subsystem weight / total incident weight, in [0, 1]."""
        intra = 0.0
        inter = 0.0
        for (a, b), w in edge_weights.items():
            a_in, b_in = a in pkgs, b in pkgs
            if a_in and b_in:
                intra += w
            elif a_in or b_in:
                inter += w
        total = intra + inter
        return min(inter / total, 1.0) if total > 0 else 0.0

    @staticmethod
    def _infer_name(pkgs, files_of_pkg):
        """Name a subsystem after its dominant package (most files).

        Common-prefix naming collides when several subsystems share a top
        directory (e.g. six distinct clusters all called "Docs Src"); the
        dominant package's path is unique and descriptive.
        """
        if not pkgs:
            return "Subsystem"
        dominant = max(pkgs, key=lambda p: (len(files_of_pkg.get(p, [])), p))
        if dominant == ".":
            return "Root"
        return dominant.replace("_", " ")
