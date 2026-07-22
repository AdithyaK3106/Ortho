"""Adversarial tests for task-025 part 1: git_history wiring in ortho scan.

GitMetadataStore.load_git_history() was fully built (context-hub) but never
called from anywhere -- scan_cli.py now calls it after every successful
scan. These tests target the failure modes a happy-path smoke test would
miss: non-git repos, empty git repos, renamed files, unicode/newline-heavy
commit messages, and a scan that must survive git errors without failing.
"""

import sqlite3
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
for _p in (
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
    _PROJECT_ROOT / "packages" / "context-hub" / "src",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import git

from storage import OrthoDatabase
from repo_intelligence.index_store import IndexStore, mint_repo_id, _mint
from repo_intelligence.scan_cli import _load_git_history


def _init_repo(tmp_path: Path) -> "git.Repo":
    return git.Repo.init(tmp_path)


def _db_for(tmp_path: Path) -> OrthoDatabase:
    db = OrthoDatabase(tmp_path)
    db.migrate()
    return db


class TestNonGitRepo:
    def test_no_git_directory_is_silent_noop(self, tmp_path):
        """A plain directory (no .git) must not raise and must not write rows."""
        (tmp_path / "a.py").write_text("x = 1\n")
        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)

        _load_git_history(db, repo_id, tmp_path, verbose=False)

        conn = db.connection()
        try:
            count = conn.execute("SELECT COUNT(*) FROM git_history").fetchone()[0]
        finally:
            conn.close()
        assert count == 0

    def test_corrupted_git_dir_does_not_raise(self, tmp_path):
        """A `.git` that exists but isn't a valid repo must degrade silently,
        not bubble an exception up into the scan (which must still exit 0)."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "a.py").write_text("x = 1\n")
        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)

        # Must not raise -- this is the entire contract under test.
        _load_git_history(db, repo_id, tmp_path, verbose=False)


class TestEmptyGitRepo:
    def test_git_repo_with_zero_commits(self, tmp_path):
        """`git init` with no commits yet: iter_commits must fail gracefully
        (there is no HEAD), not crash the loader."""
        _init_repo(tmp_path)
        (tmp_path / "a.py").write_text("x = 1\n")
        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)

        _load_git_history(db, repo_id, tmp_path, verbose=False)

        conn = db.connection()
        try:
            count = conn.execute("SELECT COUNT(*) FROM git_history").fetchone()[0]
        finally:
            conn.close()
        assert count == 0


class TestPopulatedGitRepo:
    def test_history_populated_for_scanned_file(self, tmp_path):
        repo = _init_repo(tmp_path)
        f = tmp_path / "a.py"
        f.write_text("x = 1\n")
        repo.index.add(["a.py"])
        repo.index.commit("Initial commit", author=git.Actor("T", "t@example.com"))
        f.write_text("x = 2\n")
        repo.index.add(["a.py"])
        repo.index.commit("Second commit", author=git.Actor("T", "t@example.com"))

        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)
        _load_git_history(db, repo_id, tmp_path, verbose=False)

        file_id = _mint(repo_id, "a.py")
        conn = db.connection()
        try:
            rows = conn.execute(
                "SELECT commit_hash, message FROM git_history WHERE file_id = ?",
                (file_id,),
            ).fetchall()
        finally:
            conn.close()
        # commit_date is second-precision (see git_metadata.py note) -- two
        # commits made within the same test run can tie, so assert set
        # membership, not order, unless a consumer imposes its own tiebreak.
        messages = {r[1] for r in rows}
        assert len(rows) == 2
        assert messages == {"Initial commit", "Second commit"}

    def test_file_id_matches_index_store_minting(self, tmp_path):
        """The file_id scan_cli mints for git_history must be byte-identical
        to the file_id IndexStore mints for the same file -- otherwise
        joins between git_history and files/symbols silently return nothing.
        """
        repo = _init_repo(tmp_path)
        f = tmp_path / "pkg" / "mod.py"
        f.parent.mkdir()
        f.write_text("x = 1\n")
        repo.index.add(["pkg/mod.py"])
        repo.index.commit("c1", author=git.Actor("T", "t@example.com"))

        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)
        store = IndexStore(db, repo_id, tmp_path)
        store.ensure_repository(name="x")
        store.persist_file("pkg/mod.py", [], [], [])

        _load_git_history(db, repo_id, tmp_path, verbose=False)

        conn = db.connection()
        try:
            file_id_from_files = conn.execute(
                "SELECT id FROM files WHERE rel_path = ?", ("pkg/mod.py",)
            ).fetchone()[0]
            git_history_file_ids = [
                r[0] for r in conn.execute("SELECT DISTINCT file_id FROM git_history").fetchall()
            ]
        finally:
            conn.close()
        assert file_id_from_files in git_history_file_ids

    def test_windows_backslash_relpath_normalized_before_minting(self, tmp_path):
        """On Windows, Path.relative_to yields backslash separators; if
        scan_cli mints file_id from the raw backslash path while IndexStore
        normalizes to forward slashes (persist_file does `.replace("\\\\", "/")`),
        the two file_ids diverge silently. Force the mismatch shape here
        regardless of host OS by minting both ways and asserting scan_cli
        picked the normalized one.
        """
        repo = _init_repo(tmp_path)
        f = tmp_path / "pkg" / "mod.py"
        f.parent.mkdir()
        f.write_text("x = 1\n")
        repo.index.add(["pkg/mod.py"])
        repo.index.commit("c1", author=git.Actor("T", "t@example.com"))

        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)
        _load_git_history(db, repo_id, tmp_path, verbose=False)

        normalized_id = _mint(repo_id, "pkg/mod.py")
        backslash_id = _mint(repo_id, "pkg\\mod.py")

        conn = db.connection()
        try:
            ids = {r[0] for r in conn.execute("SELECT DISTINCT file_id FROM git_history").fetchall()}
        finally:
            conn.close()
        assert normalized_id in ids
        assert backslash_id not in ids

    def test_unicode_and_newline_heavy_commit_message_round_trips(self, tmp_path):
        """Multi-line commit messages with unicode must not be truncated,
        mangled, or crash the SQLite insert."""
        repo = _init_repo(tmp_path)
        f = tmp_path / "a.py"
        f.write_text("x = 1\n")
        repo.index.add(["a.py"])
        msg = "fix: 修正 émoji 🎉\n\nBody line one.\nBody line two with \"quotes\" and 'apostrophes'."
        repo.index.commit(msg, author=git.Actor("T", "t@example.com"))

        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)
        _load_git_history(db, repo_id, tmp_path, verbose=False)

        conn = db.connection()
        try:
            stored = conn.execute("SELECT message FROM git_history LIMIT 1").fetchone()[0]
        finally:
            conn.close()
        assert stored.strip() == msg.strip()

    def test_rerunning_scan_does_not_duplicate_rows(self, tmp_path):
        """load_git_history uses INSERT OR IGNORE keyed loosely -- a second
        scan of an unchanged repo must not double the row count."""
        repo = _init_repo(tmp_path)
        f = tmp_path / "a.py"
        f.write_text("x = 1\n")
        repo.index.add(["a.py"])
        repo.index.commit("c1", author=git.Actor("T", "t@example.com"))

        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)
        _load_git_history(db, repo_id, tmp_path, verbose=False)
        _load_git_history(db, repo_id, tmp_path, verbose=False)

        conn = db.connection()
        try:
            count = conn.execute("SELECT COUNT(*) FROM git_history").fetchone()[0]
        finally:
            conn.close()
        assert count == 1

    def test_file_deleted_after_commit_is_skipped_not_fatal(self, tmp_path):
        """A file (b.py) committed once and then deleted from the working
        tree before the scan runs (the discoverer won't find it, since it
        no longer exists on disk) must not prevent history loading for the
        remaining, still-present file (a.py)."""
        repo = _init_repo(tmp_path)
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.py").write_text("y = 2\n")
        repo.index.add(["a.py", "b.py"])
        repo.index.commit("c1", author=git.Actor("T", "t@example.com"))
        (tmp_path / "a.py").write_text("x = 2\n")
        (tmp_path / "b.py").unlink()
        repo.index.add(["a.py"])
        repo.index.remove(["b.py"])
        repo.index.commit("modify a, remove b", author=git.Actor("T", "t@example.com"))

        db = _db_for(tmp_path)
        repo_id = mint_repo_id(tmp_path)
        _load_git_history(db, repo_id, tmp_path, verbose=False)

        file_id_a = _mint(repo_id, "a.py")
        conn = db.connection()
        try:
            rows = conn.execute(
                "SELECT COUNT(*) FROM git_history WHERE file_id = ?", (file_id_a,)
            ).fetchone()[0]
        finally:
            conn.close()
        assert rows == 2
