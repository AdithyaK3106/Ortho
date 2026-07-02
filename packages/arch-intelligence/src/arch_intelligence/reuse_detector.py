"""Reuse discovery: structural AST similarity between symbols (stateless).

Algorithm fully specified in
.ases/tasks/task-010-adr-awareness-reporting/spec.md ("Similarity Algorithm (ADR-010)"),
decision rationale in ADR-010.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from tree_sitter import Parser
from tree_sitter_languages import get_language

from repo_intelligence.symbol_extractor import Symbol

_LINE_BUCKET_SIZE = 5
_DEFAULT_THRESHOLD = 0.7


@dataclass
class ReuseCluster:
    """A group of structurally similar symbols (see spec.md Component 2)."""

    symbol_ids: list[str]
    file_ids: list[str]
    similarity: float
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        assert 0.0 <= self.similarity <= 1.0, "similarity must be 0.0-1.0"
        assert len(self.symbol_ids) == len(self.file_ids), "symbol_ids/file_ids length mismatch"
        assert len(self.symbol_ids) >= 2, "a cluster needs at least 2 symbols"


def _node_type_sequence(node: Any) -> list[str]:
    """Flatten a tree-sitter subtree to a sequence of node *type* labels only."""
    sequence = [node.type]
    for child in node.children:
        sequence.extend(_node_type_sequence(child))
    return sequence


def _find_symbol_node(root: Any, symbol: Symbol) -> Any | None:
    """Locate the tree-sitter node whose start line and kind match this Symbol."""
    target_types = {"function_definition"} if symbol.type in ("function", "method") else {"class_definition"}
    target_line = symbol.lineno - 1  # tree-sitter is 0-indexed, Symbol.lineno is 1-indexed

    stack = [root]
    while stack:
        node = stack.pop()
        if node.type in target_types and node.start_point[0] == target_line:
            return node
        stack.extend(node.children)
    return None


def _line_count(node: Any) -> int:
    return node.end_point[0] - node.start_point[0] + 1


def _bucket_key(symbol: Symbol, line_count: int) -> tuple[str, int]:
    """(Symbol.type, line_count // 5) — keeps pairwise comparison near-linear in practice."""
    return (symbol.type, line_count // _LINE_BUCKET_SIZE)


def _similarity(seq_a: list[str], seq_b: list[str]) -> float:
    """1 - normalized edit distance, via stdlib difflib (no new dependency by default)."""
    if not seq_a and not seq_b:
        return 1.0
    if not seq_a or not seq_b:
        return 0.0
    return SequenceMatcher(a=seq_a, b=seq_b, autojunk=False).ratio()


def _evidence_for_pair(symbol_a: Symbol, node_a: Any, symbol_b: Symbol, node_b: Any, similarity: float) -> str:
    """One evidence line citing concrete matched structural facts for a symbol pair."""
    return (
        f"{symbol_a.qualified_name} (lines {node_a.start_point[0] + 1}-{node_a.end_point[0] + 1}) "
        f"~ {symbol_b.qualified_name} (lines {node_b.start_point[0] + 1}-{node_b.end_point[0] + 1}): "
        f"similarity {similarity:.2f}, "
        f"{_line_count(node_a)} vs {_line_count(node_b)} lines, "
        f"{len(node_a.children)} vs {len(node_b.children)} top-level child nodes"
    )


class _UnionFind:
    """Minimal union-find to merge overlapping pairwise matches into clusters."""

    def __init__(self, n: int) -> None:
        self._parent = list(range(n))

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_b] = root_a


class ReuseDetector:
    """Finds structurally similar symbols via AST comparison (stateless)."""

    def find_similar(
        self,
        symbols_by_file: dict[str, list[Symbol]],
        sources_by_file: dict[str, str],
        threshold: float = _DEFAULT_THRESHOLD,
    ) -> list[ReuseCluster]:
        """See spec.md Component 2 for the full contract, edge cases, and threshold policy."""
        parser = Parser()
        parser.set_language(get_language("python"))

        # (file_path, symbol) -> parsed node + its type sequence + line count, skipping
        # symbols whose body can't be located (edge case: "Symbol with no body extractable").
        entries: list[tuple[str, Symbol, Any, list[str], int]] = []
        for file_path, symbols in symbols_by_file.items():
            source = sources_by_file.get(file_path)
            if source is None:
                continue
            tree = parser.parse(source.encode("utf-8"))
            for symbol in symbols:
                node = _find_symbol_node(tree.root_node, symbol)
                if node is None:
                    continue
                entries.append((file_path, symbol, node, _node_type_sequence(node), _line_count(node)))

        if len(entries) < 2:
            return []

        buckets: dict[tuple[str, int], list[int]] = {}
        for idx, (_, symbol, _node, _seq, line_count) in enumerate(entries):
            buckets.setdefault(_bucket_key(symbol, line_count), []).append(idx)

        # Collect every qualifying pairwise match first (idx_a, idx_b, similarity, evidence_line),
        # then merge overlapping matches into connected-component clusters (dedup near-identical
        # clusters, plan.md Task 4) instead of emitting one cluster per pair.
        pair_matches: list[tuple[int, int, float, str]] = []
        for indices in buckets.values():
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx_a, idx_b = indices[i], indices[j]
                    _, symbol_a, node_a, seq_a, _ = entries[idx_a]
                    _, symbol_b, node_b, seq_b, _ = entries[idx_b]

                    similarity = _similarity(seq_a, seq_b)
                    if similarity < threshold:
                        continue

                    pair_matches.append(
                        (
                            idx_a,
                            idx_b,
                            similarity,
                            _evidence_for_pair(symbol_a, node_a, symbol_b, node_b, similarity),
                        )
                    )

        if not pair_matches:
            return []

        uf = _UnionFind(len(entries))
        for idx_a, idx_b, _sim, _ev in pair_matches:
            uf.union(idx_a, idx_b)

        component_matches: dict[int, list[tuple[int, int, float, str]]] = {}
        for match in pair_matches:
            root = uf.find(match[0])
            component_matches.setdefault(root, []).append(match)

        clusters: list[ReuseCluster] = []
        for matches in component_matches.values():
            member_indices = sorted({idx for m in matches for idx in (m[0], m[1])})
            symbol_ids = [entries[idx][1].qualified_name for idx in member_indices]
            file_ids = [entries[idx][0] for idx in member_indices]
            # Cluster similarity is the minimum pairwise similarity within the group — the
            # honest worst-case bound for "how similar is this whole group," not an average
            # that could overstate cohesion.
            cluster_similarity = min(m[2] for m in matches)
            evidence = [m[3] for m in sorted(matches, key=lambda m: -m[2])]

            clusters.append(
                ReuseCluster(
                    symbol_ids=symbol_ids,
                    file_ids=file_ids,
                    similarity=cluster_similarity,
                    evidence=evidence,
                )
            )

        clusters.sort(key=lambda c: c.similarity, reverse=True)
        return clusters
