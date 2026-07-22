"""Adversarial tests for task-025 part 2: commit messages as decision evidence."""

import pytest

from context_hub.commit_evidence import find_relevant_commits


def _insert_commit(db, repo_id, commit_hash, message, commit_date="2026-01-01T00:00:00+00:00", author="T", file_id="f1"):
    db.execute(
        """
        INSERT INTO git_history
        (file_id, repo_id, commit_hash, author, commit_date, message,
         diff_lines_added, diff_lines_removed)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (file_id, repo_id, commit_hash, author, commit_date, message),
    )
    db.commit()


class TestFindRelevantCommits:
    def test_empty_query_returns_empty_not_everything(self, temp_db):
        """An empty query has no words to overlap with -- must not be
        treated as a wildcard that returns every commit."""
        _insert_commit(temp_db, "repo1", "a1", "fix auth bug")
        result = find_relevant_commits(temp_db, "repo1", "", limit=5)
        assert result == []

    def test_whitespace_only_query_returns_empty(self, temp_db):
        _insert_commit(temp_db, "repo1", "a1", "fix auth bug")
        result = find_relevant_commits(temp_db, "repo1", "   ", limit=5)
        assert result == []

    def test_no_matching_commits_returns_empty(self, temp_db):
        _insert_commit(temp_db, "repo1", "a1", "add unrelated feature")
        result = find_relevant_commits(temp_db, "repo1", "authentication", limit=5)
        assert result == []

    def test_matches_on_word_overlap(self, temp_db):
        _insert_commit(temp_db, "repo1", "a1", "fix auth token refresh bug")
        result = find_relevant_commits(temp_db, "repo1", "auth token", limit=5)
        assert len(result) == 1
        assert result[0].commit_hash == "a1"

    def test_repo_isolation(self, temp_db):
        """A commit in another repo must never leak into this repo's results,
        even with an identical matching message."""
        _insert_commit(temp_db, "repo1", "a1", "fix auth bug")
        _insert_commit(temp_db, "repo2", "b1", "fix auth bug")
        result = find_relevant_commits(temp_db, "repo1", "auth", limit=5)
        assert len(result) == 1
        assert result[0].commit_hash == "a1"

    def test_limit_respected(self, temp_db):
        for i in range(10):
            _insert_commit(temp_db, "repo1", f"c{i}", "fix auth bug", commit_date=f"2026-01-0{(i % 9) + 1}T00:00:00+00:00")
        result = find_relevant_commits(temp_db, "repo1", "auth", limit=3)
        assert len(result) == 3

    def test_higher_overlap_ranks_first(self, temp_db):
        _insert_commit(temp_db, "repo1", "weak", "auth", commit_date="2026-01-01T00:00:00+00:00")
        _insert_commit(temp_db, "repo1", "strong", "fix auth token refresh flow bug", commit_date="2026-01-01T00:00:00+00:00")
        result = find_relevant_commits(temp_db, "repo1", "auth token refresh", limit=5)
        assert result[0].commit_hash == "strong"

    def test_tie_broken_by_most_recent_commit_date(self, temp_db):
        _insert_commit(temp_db, "repo1", "older", "fix auth bug", commit_date="2026-01-01T00:00:00+00:00")
        _insert_commit(temp_db, "repo1", "newer", "fix auth bug", commit_date="2026-06-01T00:00:00+00:00")
        result = find_relevant_commits(temp_db, "repo1", "fix auth bug", limit=5)
        assert result[0].commit_hash == "newer"

    def test_null_message_does_not_crash(self, temp_db):
        """git commit messages are nullable in the schema -- a NULL message
        (or empty string) must be skipped, not raise on .lower() etc."""
        _insert_commit(temp_db, "repo1", "a1", None)
        result = find_relevant_commits(temp_db, "repo1", "auth", limit=5)
        assert result == []

    def test_null_author_defaults_gracefully(self, temp_db):
        temp_db.execute(
            """
            INSERT INTO git_history
            (file_id, repo_id, commit_hash, author, commit_date, message,
             diff_lines_added, diff_lines_removed)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """,
            ("f1", "repo1", "a1", None, "2026-01-01T00:00:00+00:00", "fix auth bug"),
        )
        temp_db.commit()
        result = find_relevant_commits(temp_db, "repo1", "auth", limit=5)
        assert len(result) == 1
        assert result[0].author == "unknown"

    def test_confidence_capped_at_one(self, temp_db):
        """A query fully contained in the message must not exceed
        confidence=1.0 even if the message has many more matching words
        than the query itself (Recommendation.__post_init__ raises above 1.0)."""
        _insert_commit(temp_db, "repo1", "a1", "auth auth auth auth auth bug fix flow")
        result = find_relevant_commits(temp_db, "repo1", "auth", limit=5)
        assert result[0].confidence <= 1.0

    def test_punctuation_in_message_does_not_prevent_match(self, temp_db):
        """Commit messages routinely carry punctuation (colons, parens,
        issue refs); tokenization must strip it the same way
        decision_engine._words does, or real-world messages never match."""
        _insert_commit(temp_db, "repo1", "a1", "fix(auth): resolve token-refresh bug (#123)")
        result = find_relevant_commits(temp_db, "repo1", "auth token refresh", limit=5)
        assert len(result) == 1

    def test_unicode_query_and_message(self, temp_db):
        _insert_commit(temp_db, "repo1", "a1", "fix: 認証 バグ修正")
        result = find_relevant_commits(temp_db, "repo1", "認証", limit=5)
        assert len(result) == 1

    def test_title_is_first_line_only(self, temp_db):
        _insert_commit(temp_db, "repo1", "a1", "fix auth bug\n\nLonger body text here about auth.")
        result = find_relevant_commits(temp_db, "repo1", "auth", limit=5)
        assert result[0].title == "fix auth bug"
        assert "Longer body" in result[0].description

    def test_nonexistent_repo_id_returns_empty(self, temp_db):
        _insert_commit(temp_db, "repo1", "a1", "fix auth bug")
        result = find_relevant_commits(temp_db, "nonexistent-repo", "auth", limit=5)
        assert result == []
