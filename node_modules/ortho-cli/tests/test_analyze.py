"""CLI-layer tests for `ortho analyze` — adr-check, reuse, and the --impact fix."""

import json
import subprocess
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "commands"))
from analyze import AnalyzeCommand  # noqa: E402

_ANALYZE_SCRIPT = Path(__file__).parent.parent / "src" / "commands" / "analyze.py"


def _write_adr(adr_dir: Path, filename: str, content: str) -> None:
    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / filename).write_text(content, encoding="utf-8")


def _write_py(repo_root: Path, rel_path: str, content: str) -> None:
    path = repo_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_indexed_repo(repo_root: Path, target_dependent: bool) -> None:
    """Build a minimal .ortho/ortho.db with one file and (optionally) a dependent."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared" / "storage" / "src"))
    from storage import OrthoDatabase

    db = OrthoDatabase(repo_root)
    db.migrate()
    conn = db.connection()
    conn.execute("INSERT INTO repositories (id, root_path, name) VALUES ('r1', '.', 'test')")
    conn.execute(
        "INSERT INTO files (id, repo_id, rel_path, language) VALUES ('f1', 'r1', 'auth.py', 'python')"
    )
    if target_dependent:
        conn.execute(
            "INSERT INTO files (id, repo_id, rel_path, language) VALUES ('f2', 'r1', 'routes.py', 'python')"
        )
        conn.execute(
            "INSERT INTO import_edges (importer_file_id, imported_file_id, imported_module, is_external) "
            "VALUES ('f2', 'f1', 'auth', 0)"
        )
    conn.execute(
        "INSERT INTO symbols (id, repo_id, file_id, name, qualified_name, kind, visibility, start_line, end_line) "
        "VALUES ('s1', 'r1', 'f1', 'get_user', 'get_user', 'function', 'public', 1, 5)"
    )
    conn.commit()
    conn.close()


class TestADRCheckCommand:
    def test_adr_check_command_well_formed(self, tmp_path):
        adr_dir = tmp_path / ".ases" / "architecture" / "adrs"
        _write_adr(
            adr_dir,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `x.py`.\n",
        )
        _write_py(tmp_path, "x.py", "pass")

        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_adr_check()

        assert "adrs" in result
        assert len(result["adrs"]) == 1
        assert result["adrs"][0]["classification"] == "OK"

    def test_adr_check_zero_adrs_is_valid(self, tmp_path):
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_adr_check()
        assert result == {"adrs": []}

    def test_adr_check_json_serializable(self, tmp_path):
        adr_dir = tmp_path / ".ases" / "architecture" / "adrs"
        _write_adr(adr_dir, "ADR-001-example.md", "# ADR-001: Example\n\n**Status:** ACCEPTED  \n")
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_adr_check()
        json.dumps(result)  # must not raise


class TestReuseCommand:
    def test_reuse_command_well_formed(self, tmp_path):
        src = (
            "def validate_a(x):\n    if x is None:\n        return False\n    return len(x) > 0\n\n"
            "def validate_b(y):\n    if y is None:\n        return False\n    return len(y) > 0\n"
        )
        _write_py(tmp_path, "mod.py", src)

        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_reuse()

        assert "clusters" in result
        assert len(result["clusters"]) == 1
        assert result["clusters"][0]["similarity"] == 1.0

    def test_reuse_threshold_option_changes_results(self, tmp_path):
        src = (
            "def a(x):\n    if x > 0:\n        return 1\n    return 0\n\n"
            "def b(y):\n    if y > 0:\n        return 2\n    return 3\n"
        )
        _write_py(tmp_path, "mod.py", src)

        cmd = AnalyzeCommand(tmp_path)
        loose = cmd.run_reuse(threshold=0.5)
        strict = cmd.run_reuse(threshold=1.0)

        assert len(loose["clusters"]) >= len(strict["clusters"])

    def test_reuse_zero_symbols_is_valid(self, tmp_path):
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_reuse()
        assert result == {"clusters": []}


class TestImpactCommand:
    def test_impact_fixed_not_stub(self, tmp_path):
        """Regression guard: the old stub always returned an empty report regardless of input."""
        _build_indexed_repo(tmp_path, target_dependent=True)
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_impact("auth.py")

        assert result["direct_dependents"] == ["routes.py"]  # IDs mapped to rel_paths
        assert result["risk_score"] > 0.0

    def test_impact_missing_file_no_crash(self, tmp_path):
        _build_indexed_repo(tmp_path, target_dependent=False)
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_impact("does_not_exist.py")

        assert result["direct_dependents"] == []
        assert "not found" in " ".join(result["evidence"]).lower()

    def test_impact_no_database_no_crash(self, tmp_path):
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_impact("auth.py")

        assert result["direct_dependents"] == []
        assert "not indexed" in " ".join(result["evidence"]).lower()

    def test_impact_json_serializable(self, tmp_path):
        _build_indexed_repo(tmp_path, target_dependent=True)
        cmd = AnalyzeCommand(tmp_path)
        result = cmd.run_impact("auth.py")
        json.dumps(result)  # must not raise


class TestCLIEntryPoint:
    """
    Exercises analyze.py's actual argparse entry point (_main) as a real subprocess -- the
    same code path apps/cli/src/commands/analyze.ts spawns -- rather than calling
    AnalyzeCommand methods directly in-process. Closes the gap between "the command object
    works" and "the CLI as users invoke it works" (spec.md Component 3's test names describe
    running `ortho analyze --adr-check` etc., not calling Python methods).
    """

    def _run(self, *args: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(_ANALYZE_SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def test_cli_adr_check_command(self, tmp_path):
        adr_dir = tmp_path / ".ases" / "architecture" / "adrs"
        _write_adr(adr_dir, "ADR-001-example.md", "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `x.py`.\n")
        _write_py(tmp_path, "x.py", "pass")

        result = self._run("--repo-root", str(tmp_path), "--adr-check")

        assert "adrs" in result
        assert len(result["adrs"]) == 1

    def test_cli_reuse_command(self, tmp_path):
        src = (
            "def validate_a(x):\n    if x is None:\n        return False\n    return len(x) > 0\n\n"
            "def validate_b(y):\n    if y is None:\n        return False\n    return len(y) > 0\n"
        )
        _write_py(tmp_path, "mod.py", src)

        result = self._run("--repo-root", str(tmp_path), "--reuse")

        assert "clusters" in result
        assert len(result["clusters"]) == 1

    def test_cli_reuse_threshold_option(self, tmp_path):
        src = (
            "def a(x):\n    if x > 0:\n        return 1\n    return 0\n\n"
            "def b(y):\n    if y > 0:\n        return 2\n    return 3\n"
        )
        _write_py(tmp_path, "mod.py", src)

        loose = self._run("--repo-root", str(tmp_path), "--reuse", "--threshold", "0.5")
        strict = self._run("--repo-root", str(tmp_path), "--reuse", "--threshold", "1.0")

        assert len(loose["clusters"]) >= len(strict["clusters"])

    def test_cli_impact_fixed_not_stub(self, tmp_path):
        _build_indexed_repo(tmp_path, target_dependent=True)

        result = self._run("--repo-root", str(tmp_path), "--impact", "auth.py")

        assert result["direct_dependents"] == ["routes.py"]  # IDs mapped to rel_paths
        assert result["risk_score"] > 0.0

    def test_cli_impact_missing_file(self, tmp_path):
        _build_indexed_repo(tmp_path, target_dependent=False)

        result = self._run("--repo-root", str(tmp_path), "--impact", "does_not_exist.py")

        assert result["direct_dependents"] == []

    def test_cli_json_format_all_new_commands(self, tmp_path):
        adr_dir = tmp_path / ".ases" / "architecture" / "adrs"
        _write_adr(adr_dir, "ADR-001-example.md", "# ADR-001: Example\n\n**Status:** ACCEPTED  \n")
        _write_py(tmp_path, "mod.py", "def f(x):\n    return x\n")

        adr_result = self._run("--repo-root", str(tmp_path), "--adr-check")
        reuse_result = self._run("--repo-root", str(tmp_path), "--reuse")

        json.dumps(adr_result)
        json.dumps(reuse_result)
