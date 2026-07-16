"""Cross-Repository Intelligence: real AST-structural similarity across
2+ real repos, never naming-based guesswork."""

from pathlib import Path

import pytest

from cli_commands.cross_repo import find_cross_repo_reuse


def _write_repo(root: Path, files: dict[str, str]) -> str:
    root.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        p = root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return str(root)


_VALIDATOR_A = """
def validate_input(data):
    if not data:
        raise ValueError("empty")
    if len(data) > 100:
        raise ValueError("too long")
    for item in data:
        if not isinstance(item, str):
            raise TypeError("bad type")
    return True
"""

# Structurally near-identical to _VALIDATOR_A (same shape: guard clauses +
# loop + type check), different names -- must still match on AST structure.
_VALIDATOR_B = """
def check_payload(payload):
    if not payload:
        raise ValueError("missing")
    if len(payload) > 100:
        raise ValueError("exceeds limit")
    for entry in payload:
        if not isinstance(entry, str):
            raise TypeError("wrong type")
    return True
"""

_UNRELATED = """
class Config:
    def __init__(self):
        self.debug = False
        self.timeout = 30
"""


@pytest.fixture
def repo_a(tmp_path: Path) -> str:
    return _write_repo(tmp_path / "repo_a", {"src/validator.py": _VALIDATOR_A})


@pytest.fixture
def repo_b(tmp_path: Path) -> str:
    return _write_repo(tmp_path / "repo_b", {"src/checker.py": _VALIDATOR_B})


@pytest.fixture
def repo_c_unrelated(tmp_path: Path) -> str:
    return _write_repo(tmp_path / "repo_c", {"src/config.py": _UNRELATED})


class TestCrossRepoRealMatch:
    def test_finds_genuine_structural_match_across_two_repos(self, repo_a: str, repo_b: str) -> None:
        matches = find_cross_repo_reuse([repo_a, repo_b], threshold=0.6)

        assert len(matches) >= 1
        m = matches[0]
        assert len(set(m.repos)) >= 2
        assert m.similarity >= 0.6
        assert m.evidence

    def test_match_evidence_is_real_not_fabricated(self, repo_a: str, repo_b: str) -> None:
        """Evidence must cite the actual symbols compared, not a generic
        'looks similar' claim -- matches this codebase's evidence discipline."""
        matches = find_cross_repo_reuse([repo_a, repo_b], threshold=0.6)
        assert matches
        evidence_text = " ".join(matches[0].evidence)
        assert "validate_input" in evidence_text or "check_payload" in evidence_text


class TestCrossRepoNoMatch:
    def test_unrelated_repos_produce_no_matches(self, repo_a: str, repo_c_unrelated: str) -> None:
        matches = find_cross_repo_reuse([repo_a, repo_c_unrelated], threshold=0.7)
        assert matches == []

    def test_no_match_is_not_an_error(self, repo_a: str, repo_c_unrelated: str) -> None:
        # Must return an empty list cleanly, not raise.
        result = find_cross_repo_reuse([repo_a, repo_c_unrelated], threshold=0.9)
        assert isinstance(result, list)


class TestCrossRepoAdversarial:
    def test_single_repo_raises(self, repo_a: str) -> None:
        with pytest.raises(ValueError):
            find_cross_repo_reuse([repo_a])

    def test_empty_list_raises(self) -> None:
        with pytest.raises(ValueError):
            find_cross_repo_reuse([])

    def test_too_many_repos_raises(self, tmp_path: Path) -> None:
        repos = [
            _write_repo(tmp_path / f"r{i}", {"a.py": _UNRELATED}) for i in range(6)
        ]
        with pytest.raises(ValueError):
            find_cross_repo_reuse(repos)

    def test_nonexistent_repo_path_fails_cleanly(self, repo_a: str) -> None:
        with pytest.raises(FileNotFoundError):
            find_cross_repo_reuse([repo_a, "/definitely/not/a/real/path/xyz"])

    def test_same_repo_path_twice_does_not_crash(self, repo_a: str) -> None:
        # Degenerate but should not crash: same repo counted as "2 repos".
        # Since both repo names collide, real cross-repo evidence can't be
        # established -- must return cleanly, matches or not.
        result = find_cross_repo_reuse([repo_a, repo_a], threshold=0.6)
        assert isinstance(result, list)

    def test_empty_repos_produce_no_matches_not_crash(self, tmp_path: Path) -> None:
        empty_a = _write_repo(tmp_path / "empty_a", {})
        empty_b = _write_repo(tmp_path / "empty_b", {})
        result = find_cross_repo_reuse([empty_a, empty_b])
        assert result == []

    def test_too_many_pooled_symbols_raises_before_running_comparison(self, tmp_path: Path) -> None:
        """Real, observed performance cliff (not theoretical): comparing
        click+typer whole-repo took ~11 minutes. Must fail fast with an
        actionable message instead of hanging, once pooled symbol count
        crosses the safety limit -- generate enough synthetic functions to
        cross _MAX_POOLED_SYMBOLS without needing a real large repo."""
        many_functions = "\n".join(f"def f{i}():\n    return {i}\n" for i in range(2100))
        big_a = _write_repo(tmp_path / "big_a", {"a.py": many_functions})
        small_b = _write_repo(tmp_path / "small_b", {"b.py": _VALIDATOR_A})

        with pytest.raises(ValueError, match="pool"):
            find_cross_repo_reuse([big_a, small_b])
