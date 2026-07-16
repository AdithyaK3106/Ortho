"""Accept/reject feedback loop: real ArtifactStore writes/reads, not mocks.

The roadmap's stated moat: "this recommendation was rejected three months
ago because it introduced circular dependencies." These tests verify that
sentence is actually producible end-to-end -- record a rejection with a
reason, then look it up and confirm the reason comes back, not just a
generic "seen before"."""

from pathlib import Path

import pytest

from cli_commands.feedback import lookup_feedback, record_feedback


@pytest.fixture
def repo(tmp_path: Path) -> str:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("x = 1\n", encoding="utf-8")
    return str(tmp_path)


class TestRecordFeedback:
    def test_record_accept_succeeds(self, repo: str) -> None:
        assert record_feedback(repo, "module_sizing src.foo", "accept") is True

    def test_record_reject_with_reason_succeeds(self, repo: str) -> None:
        assert record_feedback(repo, "module_sizing src.foo", "reject", "false positive, intentional") is True

    def test_invalid_decision_raises(self, repo: str) -> None:
        with pytest.raises(ValueError):
            record_feedback(repo, "module_sizing src.foo", "maybe")

    def test_empty_finding_key_raises(self, repo: str) -> None:
        with pytest.raises(ValueError):
            record_feedback(repo, "", "accept")

    def test_nonexistent_repo_returns_false_not_raise(self) -> None:
        assert record_feedback("/definitely/not/a/real/path", "x y", "accept") is False


class TestLookupFeedback:
    def test_lookup_returns_none_when_no_feedback_recorded(self, repo: str) -> None:
        assert lookup_feedback(repo, "module_sizing src.foo") is None

    def test_lookup_returns_reject_reason_after_recording(self, repo: str) -> None:
        record_feedback(repo, "module_sizing src.foo", "reject", "introduced circular dependency")

        result = lookup_feedback(repo, "module_sizing src.foo")

        assert result is not None
        assert "Rejected" in result
        assert "introduced circular dependency" in result

    def test_lookup_returns_accept_without_fabricating_a_reason(self, repo: str) -> None:
        record_feedback(repo, "module_sizing src.foo", "accept")

        result = lookup_feedback(repo, "module_sizing src.foo")

        assert result is not None
        assert "Accepted" in result

    def test_lookup_reject_with_no_reason_says_so_honestly(self, repo: str) -> None:
        record_feedback(repo, "module_sizing src.foo", "reject")

        result = lookup_feedback(repo, "module_sizing src.foo")

        assert result is not None
        assert "no reason given" in result

    def test_lookup_does_not_cross_contaminate_different_findings(self, repo: str) -> None:
        """Feedback on one finding must never leak onto a different finding
        with a similar-looking key -- an exact match, not fuzzy."""
        record_feedback(repo, "module_sizing src.foo", "reject", "reason A")
        record_feedback(repo, "module_sizing src.bar", "accept")

        foo_result = lookup_feedback(repo, "module_sizing src.foo")
        bar_result = lookup_feedback(repo, "module_sizing src.bar")

        assert foo_result is not None and "reason A" in foo_result
        assert bar_result is not None and "Accepted" in bar_result
        assert "reason A" not in bar_result

    def test_lookup_returns_most_recent_decision_when_feedback_changes(self, repo: str) -> None:
        """A developer can change their mind -- reject then later accept the
        same finding. The most recent decision should win, not the first."""
        record_feedback(repo, "module_sizing src.foo", "reject", "seemed wrong at first")
        record_feedback(repo, "module_sizing src.foo", "accept")

        result = lookup_feedback(repo, "module_sizing src.foo")

        assert result is not None
        assert "Accepted" in result

    def test_lookup_nonexistent_repo_returns_none_not_raise(self) -> None:
        assert lookup_feedback("/definitely/not/a/real/path", "x y") is None

    def test_lookup_empty_finding_key_returns_none(self, repo: str) -> None:
        assert lookup_feedback(repo, "") is None
