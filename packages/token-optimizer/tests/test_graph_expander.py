"""Tests for graph-based context expansion."""

import pytest
from token_optimizer.graph_expander import expand_by_call_graph, CallGraphInterface


class MockCallGraph(CallGraphInterface):
    """Mock call graph for testing."""

    def __init__(self, edges: dict[str, tuple[list[str], list[str]]]):
        """
        Initialize with edges dict.

        edges = {
            'authenticate': (['login'], ['hash_password', 'validate_token']),
            'login': ([], ['authenticate']),
            ...
        }

        Where value is (callers, callees)
        """
        self.edges = edges

    def get_callers(self, symbol_name: str) -> list[str]:
        """Get all symbols that call this symbol."""
        callers, _ = self.edges.get(symbol_name, ([], []))
        return callers

    def get_callees(self, symbol_name: str) -> list[str]:
        """Get all symbols this symbol calls."""
        _, callees = self.edges.get(symbol_name, ([], []))
        return callees

    def all_symbols(self) -> list[str]:
        """Get all symbol names in the graph."""
        return list(self.edges.keys())


def test_expand_query_with_matching_symbols():
    """Query containing symbol names expands with neighbors."""
    graph = MockCallGraph(
        {
            "authenticate": ([], ["hash_password", "validate_token"]),
            "hash_password": (["authenticate"], []),
            "validate_token": (["authenticate"], []),
            "login": (["authenticate"], []),
        }
    )

    query = "authenticate user"
    expanded = expand_by_call_graph(query, graph, depth=1, max_additions=10)

    # Should include original query + expanded symbols
    assert query in expanded
    assert "hash_password" in expanded
    assert "validate_token" in expanded


def test_expand_no_matching_symbols():
    """Query with no symbol matches returns original query."""
    graph = MockCallGraph(
        {
            "authenticate": ([], ["hash_password"]),
            "hash_password": (["authenticate"], []),
        }
    )

    query = "random query text"
    expanded = expand_by_call_graph(query, graph, depth=2, max_additions=10)

    # No symbols matched, return original
    assert expanded == query


def test_expand_depth_0():
    """Depth 0 returns original query."""
    graph = MockCallGraph(
        {
            "authenticate": ([], ["hash_password"]),
        }
    )

    query = "authenticate"
    expanded = expand_by_call_graph(query, graph, depth=0, max_additions=10)

    assert expanded == query


def test_expand_depth_1():
    """Depth 1 only includes direct neighbors."""
    graph = MockCallGraph(
        {
            "a": ([], ["b"]),
            "b": (["a"], ["c"]),
            "c": (["b"], []),
        }
    )

    query = "a"
    expanded = expand_by_call_graph(query, graph, depth=1, max_additions=10)

    # Depth 1 from 'a' reaches 'b' (callee of a)
    assert "b" in expanded
    # But not 'c' (would require depth 2)
    assert "c" not in expanded


def test_expand_depth_2():
    """Depth 2 includes transitive neighbors."""
    graph = MockCallGraph(
        {
            "a": ([], ["b"]),
            "b": (["a"], ["c"]),
            "c": (["b"], []),
        }
    )

    query = "a"
    expanded = expand_by_call_graph(query, graph, depth=2, max_additions=10)

    # Depth 2 from 'a' reaches 'b' and 'c'
    assert "b" in expanded
    assert "c" in expanded


def test_expand_max_additions_cap():
    """Expansion limited to max_additions."""
    graph = MockCallGraph(
        {
            "central": ([], [f"func{i}" for i in range(100)]),
            **{f"func{i}": (["central"], []) for i in range(100)},
        }
    )

    query = "central"
    expanded = expand_by_call_graph(query, graph, depth=1, max_additions=5)

    # Count how many symbols added (excluding original query)
    added = len(expanded.split()) - len(query.split())
    assert added <= 5


def test_expand_case_insensitive_matching():
    """Symbol matching is case-insensitive."""
    graph = MockCallGraph(
        {
            "Authenticate": ([], ["ValidateToken"]),
            "ValidateToken": (["Authenticate"], []),
        }
    )

    query = "authenticate user"
    expanded = expand_by_call_graph(query, graph, depth=1, max_additions=10)

    # Should match 'Authenticate' (case-insensitive)
    assert "ValidateToken" in expanded


def test_expand_deterministic_output():
    """Same input produces same output."""
    graph = MockCallGraph(
        {
            "func_a": ([], ["func_b", "func_c"]),
            "func_b": (["func_a"], []),
            "func_c": (["func_a"], []),
        }
    )

    query = "func_a"
    expanded1 = expand_by_call_graph(query, graph, depth=1, max_additions=10)
    expanded2 = expand_by_call_graph(query, graph, depth=1, max_additions=10)

    assert expanded1 == expanded2


def test_expand_circular_graph():
    """Circular dependencies handled correctly."""
    graph = MockCallGraph(
        {
            "a": (["b"], ["b"]),
            "b": (["a"], ["a"]),
        }
    )

    query = "a"
    expanded = expand_by_call_graph(query, graph, depth=2, max_additions=10)

    # Should not infinitely loop
    assert query in expanded
    # 'b' should be included (neighbor of 'a')
    assert "b" in expanded


def test_expand_empty_graph():
    """Empty graph returns original query."""
    graph = MockCallGraph({})

    query = "any query"
    expanded = expand_by_call_graph(query, graph, depth=2, max_additions=10)

    assert expanded == query


def test_expand_multiple_query_symbols():
    """Multiple symbols in query all expanded."""
    graph = MockCallGraph(
        {
            "authenticate": ([], ["validate_token"]),
            "validate_token": (["authenticate"], []),
            "hash_password": ([], ["encode"]),  # hash_password calls encode
            "encode": (["hash_password"], []),
        }
    )

    query = "authenticate and hash_password"
    expanded = expand_by_call_graph(query, graph, depth=1, max_additions=20)

    # Both original symbols expanded
    assert "validate_token" in expanded  # neighbor of authenticate
    assert "encode" in expanded  # neighbor of hash_password


def test_expand_avoids_revisiting():
    """Visited symbols not added twice."""
    graph = MockCallGraph(
        {
            "a": ([], ["b"]),
            "b": (["a"], ["c"]),
            "c": (["b"], []),
        }
    )

    query = "a"
    expanded = expand_by_call_graph(query, graph, depth=3, max_additions=50)

    # 'b' should only appear once in expanded
    words = expanded.split()
    assert words.count("b") == 1


def test_expand_preserves_original_query():
    """Expanded query contains original query."""
    graph = MockCallGraph(
        {
            "function": ([], ["related1", "related2"]),
            "related1": (["function"], []),
            "related2": (["function"], []),
        }
    )

    original = "function something"
    expanded = expand_by_call_graph(original, graph, depth=1, max_additions=10)

    # Original should be preserved at start
    assert expanded.startswith(original)


def test_expand_graph_with_missing_symbols():
    """Graph symbols not in query not expanded."""
    graph = MockCallGraph(
        {
            "search": ([], ["index"]),
            "index": (["search"], []),
            "unrelated": ([], []),
        }
    )

    query = "search results"
    expanded = expand_by_call_graph(query, graph, depth=1, max_additions=10)

    # 'unrelated' should NOT be in expanded (not in query, not a neighbor)
    assert "unrelated" not in expanded
    # 'index' SHOULD be in expanded (neighbor of 'search')
    assert "index" in expanded
