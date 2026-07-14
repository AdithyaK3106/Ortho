"""Layer detection via topological sort."""

from typing import Optional
from .types import Layer

# Path segments (exact match, case-insensitive) identifying non-production
# code. Files under any of these directories are excluded from layer
# assignment entirely — they are not part of the architecture being
# evaluated, and including them causes test/example files that import
# production code to be misclassified as architectural layer violations.
_EXCLUDED_SEGMENTS = frozenset({
    "tests", "test", "examples", "example", "__tests__", "vendor", "node_modules",
})


def _is_excluded(rel_path: str) -> bool:
    segments = rel_path.replace("\\", "/").split("/")
    return any(segment.lower() in _EXCLUDED_SEGMENTS for segment in segments)


class LayerDetector:
    """Extracts architectural layers from import graph."""

    SEMANTIC_KEYWORDS = {
        0: ["repository", "model", "db", "dao", "persistence"],
        1: ["service", "business", "logic", "domain", "core"],
        2: ["controller", "view", "endpoint", "handler", "api"],
    }

    def extract_layers(self, import_graph: list, files: list) -> list[Layer]:
        """
        Extract layers from import DAG via topological sort.
        Layer 0 = data (no outgoing), Layer 1 = business, Layer 2 = presentation.

        Files under test/example/vendor directories (see _EXCLUDED_SEGMENTS)
        are excluded entirely — they are not production architecture.
        """
        files = [f for f in files if not _is_excluded(f.rel_path)]

        if not files:
            return []

        file_map = {f.id: f for f in files}

        # Build adjacency (internal imports only)
        file_ids = {f.id for f in files}
        imports: dict = {fid: set() for fid in file_ids}
        
        for edge in import_graph:
            if edge.importer_file_id in file_ids and edge.imported_file_id in file_ids:
                imports[edge.importer_file_id].add(edge.imported_file_id)

        # Topological sort: Kahn's algorithm
        in_degree = {fid: 0 for fid in file_ids}
        for fid in file_ids:
            for target in imports[fid]:
                in_degree[target] += 1

        queue = [fid for fid in file_ids if in_degree[fid] == 0]
        topo_order = []
        
        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for target in imports[node]:
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)

        # Assign layer numbers (0 = deepest, no incoming)
        file_to_layer = {}
        for fid in topo_order:
            deps = [file_to_layer.get(target, 0) for target in imports[fid]]
            file_to_layer[fid] = max(deps) + 1 if deps else 0

        # Group by layer
        layers_dict: dict = {}
        for fid, layer_num in file_to_layer.items():
            if layer_num not in layers_dict:
                layers_dict[layer_num] = []
            layers_dict[layer_num].append(fid)

        # Create Layer objects
        layers = []
        for layer_num in sorted(layers_dict.keys()):
            file_ids_in_layer = layers_dict[layer_num]
            name = self._infer_layer_name(layer_num, file_ids_in_layer, file_map)
            
            depends_on = []
            for fid in file_ids_in_layer:
                for imported in imports[fid]:
                    if imported in file_to_layer:
                        dep_layer = file_to_layer[imported]
                        if dep_layer not in depends_on and dep_layer != layer_num:
                            depends_on.append(dep_layer)

            layer = Layer(
                id=f"layer_{layer_num}",
                number=layer_num,
                name=name,
                file_ids=file_ids_in_layer,
                depends_on=depends_on,
            )
            layers.append(layer)

        return layers

    def _infer_layer_name(self, layer_num: int, file_ids: list, file_map: dict) -> str:
        """Infer layer name from semantic keywords in file paths."""
        if layer_num == 0:
            return "Data"
        elif layer_num == 1:
            return "Business"
        elif layer_num == 2:
            return "Presentation"
        
        # Check semantic keywords
        for fid in file_ids:
            path = file_map.get(fid, type('', (), {'rel_path': ''})()).rel_path.lower()
            for keyword in self.SEMANTIC_KEYWORDS.get(layer_num, []):
                if keyword in path:
                    return keyword.capitalize()
        
        return f"Layer {layer_num}"
