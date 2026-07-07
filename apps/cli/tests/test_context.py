"""CLI-layer tests for `ortho context add|search` — the context.py argparse bridge.

Derived STRICTLY from task-011 spec.md (CLI contract + bridge protocol) and plan.md AC4.
Style mirrors test_analyze.py: the bridge is exercised as a real subprocess — the same
code path apps/cli/src/commands/context.ts spawns — never by importing bridge internals.

Contract under test (spec.md):
    ortho context add --title <t> --content <c> [--type note] [--source manual] [--tags a,b]
    ortho context search <query> [--limit 10] [--type <t>] [--format text|json]
Protocol: one JSON object on stdout, exit 0 on success (same as analyze.py).
`add` prints {"artifact_id": ..., "version": ...}.
AC4: add then search works against a migration-002 database.
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_CONTEXT_SCRIPT = Path(__file__).parent.parent / "src" / "commands" / "context.py"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_STORAGE_SRC = _PROJECT_ROOT / "shared" / "storage" / "src"
if str(_STORAGE_SRC) not in sys.path:
    sys.path.insert(0, str(_STORAGE_SRC))

from storage import OrthoDatabase  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    """A repo root with a migration-002 database (AC4: 'against a migration-002
    database') — created through the real OrthoDatabase.migrate(), never hand-built."""
    OrthoDatabase(tmp_path).migrate()
    return tmp_path


def _run_raw(*args: str) -> subprocess.CompletedProcess:
    """Invoke the bridge exactly as the TS command spawns it."""
    return subprocess.run(
        [sys.executable, str(_CONTEXT_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def _run_json(*args: str):
    """Invoke the bridge and parse its single JSON stdout payload; exit must be 0."""
    result = _run_raw(*args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _add(repo_root: Path, title: str, content: str, *extra: str) -> dict:
    """Run `context add` and return the parsed {"artifact_id", "version"} object."""
    return _run_json(
        "--repo-root", str(repo_root), "add", "--title", title, "--content", content, *extra
    )


def _search(repo_root: Path, query: str, *extra: str) -> list:
    """Run `context search --format json` and normalize the results list.

    Spec says the bridge prints one JSON object; the results-list key shape is
    an interpretation (dict-with-'results' or bare list are both accepted here,
    flagged for the API CONTRACT GATE).
    """
    payload = _run_json("--repo-root", str(repo_root), "search", query, "--format", "json", *extra)
    if isinstance(payload, dict):
        results = payload.get("results")
        assert isinstance(results, list), f"search payload has no results list: {payload}"
        return results
    assert isinstance(payload, list)
    return payload


def _artifact_row(repo_root: Path, artifact_id: str, columns: str) -> tuple:
    """Read one artifacts row directly from the migrated DB (verifies persistence)."""
    conn = sqlite3.connect(str(repo_root / ".ortho" / "ortho.db"))
    try:
        return conn.execute(
            f"SELECT {columns} FROM artifacts WHERE id = ? ORDER BY version DESC LIMIT 1",
            (artifact_id,),
        ).fetchone()
    finally:
        conn.close()


class TestContextAdd:
    """`context add` protocol: JSON {"artifact_id", "version"}, exit 0."""

    def test_sample_context_add_prints_json(self, repo):
        """PILOT SAMPLE (AC4): add prints one JSON object with artifact_id and
        version == 1, exit code 0."""
        payload = _add(repo, "Auth notes", "JWT tokens rotate hourly", "--type", "dev_note")
        assert isinstance(payload, dict)
        assert isinstance(payload["artifact_id"], str)
        assert payload["artifact_id"] != ""
        assert payload["version"] == 1

    def test_add_twice_same_content_returns_same_artifact_id(self, repo):
        """Versioning contract: identical repo/title/source/content → same artifact_id,
        no new version minted for unchanged content."""
        first = _add(repo, "Stable note", "identical content payload")
        second = _add(repo, "Stable note", "identical content payload")
        assert first["artifact_id"] == second["artifact_id"]

    def test_add_persists_row_in_migration_002_db(self, repo):
        """The added artifact lands in the canonical artifacts table with version 1."""
        payload = _add(repo, "Persisted note", "row-level persistence check")
        row = _artifact_row(repo, payload["artifact_id"], "title, content, version")
        assert row is not None
        assert row[0] == "Persisted note"
        assert row[1] == "row-level persistence check"
        assert row[2] == 1

    def test_add_tags_comma_split_persisted(self, repo):
        """--tags a,b is split on commas and stored as a JSON list."""
        payload = _add(repo, "Tagged note", "content with tags", "--tags", "alpha,beta")
        row = _artifact_row(repo, payload["artifact_id"], "tags")
        assert row is not None
        assert json.loads(row[0]) == ["alpha", "beta"]

    def test_add_default_source_is_manual(self, repo):
        """Omitting --source stores the spec default 'manual'."""
        payload = _add(repo, "Sourceless note", "default source check")
        row = _artifact_row(repo, payload["artifact_id"], "source")
        assert row is not None
        assert row[0] == "manual"

    def test_add_default_type_accepted(self, repo):
        """Omitting --type (default note) still succeeds and is searchable (AC4)."""
        _add(repo, "Untyped note", "quokka default type content")
        results = _search(repo, "quokka")
        assert len(results) == 1

    def test_add_missing_content_exits_nonzero(self, repo):
        """add without required --content fails with a nonzero exit code."""
        result = _run_raw("--repo-root", str(repo), "add", "--title", "Only title")
        assert result.returncode != 0

    def test_add_missing_title_exits_nonzero(self, repo):
        """add without required --title fails with a nonzero exit code."""
        result = _run_raw("--repo-root", str(repo), "add", "--content", "Only content")
        assert result.returncode != 0


class TestContextSearch:
    """`context search` finds added artifacts via BM25 against the migrated DB."""

    def test_search_returns_added_artifact(self, repo):
        """AC4 round trip: add with a unique token, search that token → the artifact."""
        added = _add(repo, "Zebra doc", "the zebrasearchtoken appears here", "--type", "dev_note")
        results = _search(repo, "zebrasearchtoken")
        assert len(results) == 1
        assert results[0]["artifact_id"] == added["artifact_id"]
        assert results[0]["title"] == "Zebra doc"

    def test_search_no_results_returns_empty_list(self, repo):
        """A query matching nothing returns an empty results list with exit 0."""
        results = _search(repo, "nonexistenttokenxyzzy")
        assert results == []

    def test_search_limit_caps_results(self, repo):
        """--limit 2 returns exactly 2 of 3 matching artifacts."""
        for i in range(3):
            _add(repo, f"Doc {i}", f"sharedlimittoken document number {i}")
        results = _search(repo, "sharedlimittoken", "--limit", "2")
        assert len(results) == 2

    def test_search_type_filter(self, repo):
        """--type restricts results to artifacts of that type."""
        adr = _add(repo, "ADR entry", "typedfiltertoken adr flavored", "--type", "adr")
        _add(repo, "Decision entry", "typedfiltertoken decision flavored", "--type", "decision")
        results = _search(repo, "typedfiltertoken", "--type", "adr")
        assert len(results) == 1
        assert results[0]["artifact_id"] == adr["artifact_id"]

    def test_search_format_text_exits_zero(self, repo):
        """--format text is accepted: exit 0 and non-empty stdout."""
        _add(repo, "Text format doc", "textformattoken lives here")
        result = _run_raw(
            "--repo-root", str(repo), "search", "textformattoken", "--format", "text"
        )
        assert result.returncode == 0
        assert result.stdout.strip() != ""

    def test_search_missing_query_exits_nonzero(self, repo):
        """search without the positional query fails with a nonzero exit code."""
        result = _run_raw("--repo-root", str(repo), "search")
        assert result.returncode != 0
