"""Graph-based context expansion using call graph neighbors."""

from typing import List, Dict, Set


class CallGraphInterface:
    """Minimal interface for call graph queries.

    This interface abstracts the call graph so token-optimizer
    doesn't depend directly on repo-intelligence.
    """

    def get_callers(self, symbol_name: str) -> List[str]:
        """Get all symbols that call this symbol."""
        raise NotImplementedError

    def get_callees(self, symbol_name: str) -> List[str]:
        """Get all symbols this symbol calls."""
        raise NotImplementedError

    def all_symbols(self) -> List[str]:
        """Get all symbol names in the graph."""
        raise NotImplementedError


def expand_by_call_graph(
    query: str,
    call_graph: CallGraphInterface,
    depth: int = 2,
    max_additions: int = 20,
) -> str:
    """
    Expand query by finding related symbols in call graph.

    Strategy:
    - Parse query to extract symbol names (simple word-based)
    - For each query word, check if it's a symbol in call_graph
    - If found, perform BFS traversal up to `depth` hops
    - Collect callers and callees
    - Add top `max_additions` related symbols to query
    - Return expanded query string

    Args:
        query: Original search query
        call_graph: CallGraphInterface instance
        depth: Graph traversal depth (1-based, default 2)
        max_additions: Max symbols to add (default 20)

    Returns:
        Expanded query string (original + related symbols)

    Example:
        query = "authenticate user"
        expanded = expand_by_call_graph(query, graph, depth=2, max_additions=10)
        # Result: "authenticate user validate_token hash_password ..."
    """
    if depth < 1:
        return query

    # Extract candidate symbol names from query (case-insensitive)
    query_lower = query.lower()
    query_words = query_lower.split()

    # Get all symbol names from graph
    all_symbols = call_graph.all_symbols()
    all_symbols_lower = {s.lower(): s for s in all_symbols}

    # Find which query words are symbols in the graph
    matching_symbols: Set[str] = set()
    for word in query_words:
        if word in all_symbols_lower:
            matching_symbols.add(all_symbols_lower[word])

    if not matching_symbols:
        # No symbols found in query; return original query
        return query

    # BFS to collect related symbols
    related: Set[str] = set()
    visited: Set[str] = set(matching_symbols)
    queue: List[tuple[str, int]] = [(s, 0) for s in matching_symbols]

    while queue and len(related) < max_additions:
        symbol, current_depth = queue.pop(0)

        # Don't add the symbol if we're at or beyond max depth
        if current_depth < depth:
            # Get neighbors
            try:
                callers = call_graph.get_callers(symbol)
                callees = call_graph.get_callees(symbol)
            except Exception:
                # If graph lookup fails, skip this symbol
                callers = []
                callees = []

            # Add neighbors to queue (if not visited)
            for neighbor in callers + callees:
                if neighbor not in visited and len(related) < max_additions:
                    visited.add(neighbor)
                    related.add(neighbor)
                    queue.append((neighbor, current_depth + 1))

    # Build expanded query
    if related:
        expanded_symbols = sorted(related)  # Deterministic ordering
        return f"{query} {' '.join(expanded_symbols)}"
    else:
        return query
