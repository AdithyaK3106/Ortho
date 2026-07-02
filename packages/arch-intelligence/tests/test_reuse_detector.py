"""ReuseDetector tests — fixture-based, deterministic per spec.md/ADR-010."""

import time

import pytest
from hypothesis import given, settings, strategies as st

from repo_intelligence.symbol_extractor import SymbolExtractor
from arch_intelligence.reuse_detector import ReuseDetector


def _symbols_and_sources(sources: dict[str, str]) -> tuple[dict, dict]:
    extractor = SymbolExtractor()
    symbols_by_file = {
        path: extractor.extract_symbols(path, src) for path, src in sources.items()
    }
    return symbols_by_file, dict(sources)


SRC_VALIDATE_USER = """
def validate_user(name):
    if name is None:
        return False
    return len(name) > 0
"""

SRC_VALIDATE_ACCOUNT = """
def validate_account(account_id):
    if account_id is None:
        return False
    return len(account_id) > 0
"""

SRC_UNRELATED = """
def totally_different(x, y, z):
    for i in range(x):
        print(i)
    return x + y + z
"""


@pytest.fixture
def detector():
    return ReuseDetector()


class TestReuseDetectorUnit:
    def test_identical_functions_different_names(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources(
            {"a.py": SRC_VALIDATE_USER, "b.py": SRC_VALIDATE_ACCOUNT}
        )
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        assert len(clusters) == 1
        assert clusters[0].similarity == 1.0
        assert set(clusters[0].symbol_ids) == {"validate_user", "validate_account"}

    def test_unrelated_functions_not_clustered(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources(
            {"a.py": SRC_VALIDATE_USER, "c.py": SRC_UNRELATED}
        )
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        assert clusters == []

    def test_threshold_boundary_included(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources(
            {"a.py": SRC_VALIDATE_USER, "b.py": SRC_VALIDATE_ACCOUNT}
        )
        clusters = detector.find_similar(symbols_by_file, sources_by_file, threshold=1.0)
        assert len(clusters) == 1

    def test_empty_input(self, detector):
        assert detector.find_similar({}, {}) == []

    def test_single_symbol(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": SRC_VALIDATE_USER})
        assert detector.find_similar(symbols_by_file, sources_by_file) == []

    def test_same_file_duplicates_clustered(self, detector):
        src = SRC_VALIDATE_USER + "\n\ndef validate_thing(thing):\n    if thing is None:\n        return False\n    return len(thing) > 0\n"
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": src})
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        assert len(clusters) == 1
        assert clusters[0].file_ids == ["a.py", "a.py"]

    def test_bucketing_skips_size_mismatch(self, detector):
        tiny = "\ndef f():\n    return 1\n"
        huge_lines = "\n".join(f"    x{i} = {i}" for i in range(60))
        huge = f"\ndef g():\n{huge_lines}\n    return 1\n"
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": tiny, "b.py": huge})
        clusters = detector.find_similar(symbols_by_file, sources_by_file, threshold=0.0)
        # Wildly different sizes land in different line-count buckets and are never compared,
        # even at threshold 0.0 (a low threshold would otherwise cluster nearly anything).
        assert clusters == []

    def test_cluster_evidence_present(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources(
            {"a.py": SRC_VALIDATE_USER, "b.py": SRC_VALIDATE_ACCOUNT}
        )
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        assert all(c.evidence for c in clusters)

    def test_dedup_merges_mutually_similar_group(self, detector):
        src = "\n".join(
            f"def validate_{name}({name}):\n    if {name} is None:\n        return False\n    return len({name}) > 0\n"
            for name in ("a", "b", "c")
        )
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": src})
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        # Without dedup this would fragment into 3 separate pairwise clusters (a~b, a~c, b~c).
        assert len(clusters) == 1
        assert set(clusters[0].symbol_ids) == {"validate_a", "validate_b", "validate_c"}
        assert len(clusters[0].evidence) == 3

    def test_evidence_cites_line_ranges(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources(
            {"a.py": SRC_VALIDATE_USER, "b.py": SRC_VALIDATE_ACCOUNT}
        )
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        assert "lines" in clusters[0].evidence[0]
        assert "validate_user" in clusters[0].evidence[0]
        assert "validate_account" in clusters[0].evidence[0]


class TestReuseDetectorIntegration:
    def test_finds_known_duplicate_pair(self, detector):
        symbols_by_file, sources_by_file = _symbols_and_sources(
            {"a.py": SRC_VALIDATE_USER, "b.py": SRC_VALIDATE_ACCOUNT, "c.py": SRC_UNRELATED}
        )
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        assert len(clusters) == 1
        assert set(clusters[0].symbol_ids) == {"validate_user", "validate_account"}

    def test_symbol_set_scales(self, detector):
        # ~100 symbols across 20 files: generous ceiling per spec.md's Benchmark Environment
        # policy — not an exact benchmark value, just a regression guard against losing bucketing.
        sources = {}
        for i in range(20):
            body = "\n".join(
                f"def func_{i}_{j}(x):\n    if x > {j}:\n        return x\n    return {j}"
                for j in range(5)
            )
            sources[f"file_{i}.py"] = body
        symbols_by_file, sources_by_file = _symbols_and_sources(sources)

        start = time.monotonic()
        clusters = detector.find_similar(symbols_by_file, sources_by_file)
        elapsed = time.monotonic() - start

        assert elapsed < 10.0
        assert isinstance(clusters, list)


_BLOCK_KINDS = ("if", "for", "nested_if")


def _random_block(kind: str, count: int) -> str:
    """Generate a body of `count` statements of the given control-flow shape."""
    if kind == "if":
        return "\n".join(f"    if x > {i}:\n        return {i}" for i in range(count))
    if kind == "for":
        return "\n".join(f"    for i{i} in range({i}):\n        pass" for i in range(count))
    # nested_if: chains of nesting instead of sibling branches
    body = "    return -1"
    for i in range(count):
        body = f"    if x > {i}:\n" + "\n".join("    " + line for line in body.splitlines())
    return body


_shape_strategy = st.tuples(st.sampled_from(_BLOCK_KINDS), st.integers(min_value=0, max_value=6))


class TestReuseDetectorProperties:
    @given(_shape_strategy)
    @settings(max_examples=15)
    def test_similarity_bounds(self, shape):
        kind, count = shape
        body = _random_block(kind, count)
        src_a = f"def f(x):\n{body}\n    return -1\n"
        src_b = f"def g(y):\n{body}\n    return -1\n"
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": src_a, "b.py": src_b})
        detector = ReuseDetector()
        clusters = detector.find_similar(symbols_by_file, sources_by_file, threshold=0.0)
        for c in clusters:
            assert 0.0 <= c.similarity <= 1.0

    @given(_shape_strategy)
    @settings(max_examples=15)
    def test_deterministic(self, shape):
        kind, count = shape
        body = _random_block(kind, count)
        src = f"def f(x):\n{body}\n    return -1\n"
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": src, "b.py": src.replace("f(x)", "g(x)")})
        detector = ReuseDetector()
        run1 = detector.find_similar(symbols_by_file, sources_by_file)
        run2 = detector.find_similar(symbols_by_file, sources_by_file)
        assert run1 == run2

    @given(_shape_strategy, _shape_strategy)
    @settings(max_examples=15)
    def test_symmetry(self, shape_a, shape_b):
        kind_a, count_a = shape_a
        kind_b, count_b = shape_b
        src_a = f"def f(x):\n{_random_block(kind_a, count_a)}\n    return -1\n"
        src_b = f"def g(x):\n{_random_block(kind_b, count_b)}\n    return -1\n"

        detector = ReuseDetector()
        symbols_fwd, sources_fwd = _symbols_and_sources({"a.py": src_a, "b.py": src_b})
        symbols_rev, sources_rev = _symbols_and_sources({"a.py": src_b, "b.py": src_a})

        fwd = detector.find_similar(symbols_fwd, sources_fwd, threshold=0.0)
        rev = detector.find_similar(symbols_rev, sources_rev, threshold=0.0)

        fwd_sim = fwd[0].similarity if fwd else None
        rev_sim = rev[0].similarity if rev else None
        assert fwd_sim == rev_sim

    @given(st.integers(min_value=2, max_value=8))
    @settings(max_examples=10)
    def test_varying_symbol_counts_no_crash(self, n):
        """(+1 of the '7 more' spec.md calls for: varying symbol counts.)"""
        sources = {
            f"f{i}.py": f"def func_{i}(x):\n    if x > {i % 3}:\n        return {i}\n    return 0\n"
            for i in range(n)
        }
        symbols_by_file, sources_by_file = _symbols_and_sources(sources)
        detector = ReuseDetector()
        clusters = detector.find_similar(symbols_by_file, sources_by_file, threshold=0.0)
        assert isinstance(clusters, list)
        for c in clusters:
            assert 0.0 <= c.similarity <= 1.0

    @given(st.floats(min_value=0.0, max_value=1.0))
    @settings(max_examples=10)
    def test_threshold_sweep_monotonic(self, threshold):
        """(+1 of the '7 more': threshold sweeps — higher threshold never yields more clusters.)"""
        src_a = "def f(x):\n    if x > 0:\n        return 1\n    return 0\n"
        src_b = "def g(y):\n    if y > 0:\n        return 1\n    return 0\n"
        symbols_by_file, sources_by_file = _symbols_and_sources({"a.py": src_a, "b.py": src_b})
        detector = ReuseDetector()
        loose = detector.find_similar(symbols_by_file, sources_by_file, threshold=0.0)
        strict = detector.find_similar(symbols_by_file, sources_by_file, threshold=threshold)
        assert len(strict) <= len(loose)


def test_reuse_cluster_order_independent_of_input_order(detector):
    """
    Regression test for Finding 1 (test-plan.md GATE 4 audit): find_similar()'s *scoring* is
    symmetric and deterministic (test_symmetry, test_deterministic already cover that); this
    verifies cluster *order* in the returned list is also independent of symbols_by_file's dict
    insertion order when two+ clusters tie in similarity -- the CLI's run_reuse() builds that
    dict from Path.rglob(), which has no ordering guarantee. Fixed via a secondary sort key
    (sorted symbol_ids) on find_similar()'s final sort.
    """
    src_a = (
        "def a(x):\n    if x > 0:\n        return 1\n    return 0\n\n"
        "def b(y):\n    if y > 0:\n        return 1\n    return 0\n"
    )
    src_b = (
        "def m(p):\n    for i in range(p):\n        print(i)\n\n"
        "def n(q):\n    for i in range(q):\n        print(i)\n"
    )

    symbols_by_file_1, sources_by_file_1 = _symbols_and_sources({"f1.py": src_a, "f2.py": src_b})
    symbols_by_file_2, sources_by_file_2 = _symbols_and_sources({"f2.py": src_b, "f1.py": src_a})

    clusters_1 = detector.find_similar(symbols_by_file_1, sources_by_file_1, threshold=0.5)
    clusters_2 = detector.find_similar(symbols_by_file_2, sources_by_file_2, threshold=0.5)

    assert [c.symbol_ids for c in clusters_1] == [c.symbol_ids for c in clusters_2]

    # TARGET for BUILDER's fix (Finding 1) -- currently would FAIL, left as documentation:
    # assert [c.symbol_ids for c in clusters_1] == [c.symbol_ids for c in clusters_2]
