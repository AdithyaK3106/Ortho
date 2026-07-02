"""ADRTracker tests — fixture-based, repository-independent per spec.md."""

from pathlib import Path

import pytest

from arch_intelligence.adr_tracker import ADRTracker, ADRStatus
from arch_intelligence.types import ArchitectureModel, ArchStyle, Subsystem


def _write_adr(tmp_path: Path, filename: str, content: str) -> Path:
    adr_dir = tmp_path / "adrs"
    adr_dir.mkdir(exist_ok=True)
    path = adr_dir / filename
    path.write_text(content, encoding="utf-8")
    return adr_dir


@pytest.fixture
def tracker():
    return ADRTracker()


class TestADRTrackerUnit:
    def test_parse_status_accepted(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n**Date:** 2026-01-01\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].status == "ACCEPTED"

    def test_parse_status_missing(self, tmp_path, tracker):
        adr_dir = _write_adr(tmp_path, "ADR-001-example.md", "# ADR-001: Example\n\nNo status here.\n")
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].status == "UNKNOWN"

    def test_extract_backtick_paths(self, tmp_path, tracker):
        (tmp_path / "shared").mkdir()
        (tmp_path / "shared" / "adapter.ts").write_text("x")
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `shared/adapter.ts` for details.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert "shared/adapter.ts" in results[0].referenced_paths

    def test_extract_file_line_precedence(self, tmp_path, tracker):
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "mod.py").write_text("x")
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\n"
            "File: pkg/mod.py\n\nAlso mentioned inline as `pkg/mod.py`.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].referenced_paths.count("pkg/mod.py") == 1

    def test_extract_markdown_link(self, tmp_path, tracker):
        (tmp_path / "packages" / "foo").mkdir(parents=True)
        (tmp_path / "packages" / "foo" / "bar.py").write_text("x")
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\n"
            "[bar module](packages/foo/bar.py) and [anchor](#section) "
            "and [ext](https://example.com).\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert "packages/foo/bar.py" in results[0].referenced_paths
        assert not any("example.com" in p for p in results[0].referenced_paths)
        assert not any(p.startswith("#") for p in results[0].referenced_paths)

    def test_classify_ok(self, tmp_path, tracker):
        (tmp_path / "a.py").write_text("x")
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `a.py`.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].classification == "OK"
        assert results[0].missing_paths == []

    def test_classify_stale(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `missing/file.py`.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].classification == "STALE"
        assert "missing/file.py" in results[0].missing_paths

    def test_classify_unlinked(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nNo code paths mentioned at all.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].classification == "UNLINKED"

    def test_glob_and_url_skipped(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\n"
            "See `packages/*/tests/` and `https://example.com/readme.md`.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].referenced_paths == []
        assert results[0].missing_paths == []
        assert results[0].classification == "UNLINKED"


class TestADRTrackerIntegration:
    def test_directory_with_n_adrs(self, tmp_path, tracker):
        for i in range(1, 4):
            _write_adr(
                tmp_path,
                f"ADR-{i:03d}-example.md",
                f"# ADR-{i:03d}: Example {i}\n\n**Status:** ACCEPTED  \n\nSee `a{i}.py`.\n",
            )
            (tmp_path / f"a{i}.py").write_text("x")
        adr_dir = tmp_path / "adrs"
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert len(results) == 3
        assert all(r.classification == "OK" for r in results)

    def test_empty_dir(self, tmp_path, tracker):
        results = tracker.check_adrs(tmp_path / "nonexistent", tmp_path)
        assert results == []

    def test_deterministic_repeat_run(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `a.py` and `b.py`.\n",
        )
        (tmp_path / "a.py").write_text("x")
        run1 = tracker.check_adrs(adr_dir, tmp_path)
        run2 = tracker.check_adrs(adr_dir, tmp_path)
        assert run1 == run2

    def test_deterministic_across_extraction_order(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\n"
            "File: shared/x.py\n\nAlso `shared/x.py` inline, and [link](shared/x.py).\n",
        )
        (tmp_path / "shared").mkdir()
        (tmp_path / "shared" / "x.py").write_text("x")
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].referenced_paths == ["shared/x.py"]


class TestADRTrackerEdgeCases:
    def test_malformed_markdown(self, tmp_path, tracker):
        adr_dir = _write_adr(tmp_path, "ADR-001-example.md", "just some random text\nno headers\n")
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert len(results) == 1
        assert results[0].status == "UNKNOWN"

    def test_unreadable_file_does_not_crash(self, tmp_path, tracker, monkeypatch):
        """OSError during read (permissions, race with deletion) degrades gracefully."""
        adr_dir = _write_adr(tmp_path, "ADR-001-example.md", "# ADR-001: Example\n\n**Status:** ACCEPTED  \n")

        original_read_text = Path.read_text

        def _flaky_read_text(self, *args, **kwargs):
            if self.name == "ADR-001-example.md":
                raise OSError("simulated read failure")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", _flaky_read_text)

        results = tracker.check_adrs(adr_dir, tmp_path)
        assert len(results) == 1
        assert results[0].status == "UNKNOWN"
        assert results[0].classification == "UNKNOWN"
        assert "Could not read" in results[0].evidence[0]

    def test_null_byte_in_candidate_dropped_silently(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nSee `a\x00b.py`.\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].referenced_paths == []
        assert results[0].classification == "UNLINKED"

    def test_candidate_with_only_whitespace_rejected(self, tmp_path, tracker):
        adr_dir = _write_adr(
            tmp_path,
            "ADR-001-example.md",
            "# ADR-001: Example\n\n**Status:** ACCEPTED  \n\nFile: not a path just words\n",
        )
        results = tracker.check_adrs(adr_dir, tmp_path)
        assert results[0].referenced_paths == []


def _model_with_subsystems(*subsystems: Subsystem) -> ArchitectureModel:
    return ArchitectureModel(
        repo_id="repo",
        style=ArchStyle.LAYERED,
        style_confidence=0.9,
        subsystems=list(subsystems),
    )


class TestSubsystemCoverage:
    def test_small_subsystem_omitted(self, tracker):
        small = Subsystem(id="s1", name="small", file_ids=["a.py", "b.py", "c.py"])
        model = _model_with_subsystems(small)
        results = tracker.check_subsystem_coverage([], model)
        assert results == []

    def test_large_subsystem_with_owning_adr(self, tracker):
        large = Subsystem(id="s1", name="large", file_ids=["a.py", "b.py", "c.py", "d.py"])
        model = _model_with_subsystems(large)
        adr_statuses = [
            ADRStatus(adr_id="ADR-001", title="", status="ACCEPTED", referenced_paths=["a.py"])
        ]
        results = tracker.check_subsystem_coverage(adr_statuses, model)
        assert len(results) == 1
        assert results[0].has_owning_adr is True
        assert results[0].owning_adr_ids == ["ADR-001"]

    def test_large_subsystem_without_owning_adr(self, tracker):
        large = Subsystem(id="s1", name="large", file_ids=["a.py", "b.py", "c.py", "d.py"])
        model = _model_with_subsystems(large)
        adr_statuses = [
            ADRStatus(adr_id="ADR-001", title="", status="ACCEPTED", referenced_paths=["unrelated.py"])
        ]
        results = tracker.check_subsystem_coverage(adr_statuses, model)
        assert len(results) == 1
        assert results[0].has_owning_adr is False
        assert results[0].owning_adr_ids == []

    def test_empty_model_returns_empty(self, tracker):
        model = _model_with_subsystems()
        results = tracker.check_subsystem_coverage([], model)
        assert results == []

    def test_threshold_boundary_exactly_three_omitted(self, tracker):
        boundary = Subsystem(id="s1", name="boundary", file_ids=["a.py", "b.py", "c.py"])
        model = _model_with_subsystems(boundary)
        results = tracker.check_subsystem_coverage([], model)
        assert results == []

    def test_multiple_subsystems_sorted_by_id(self, tracker):
        s_b = Subsystem(id="s-b", name="b", file_ids=["1.py", "2.py", "3.py", "4.py"])
        s_a = Subsystem(id="s-a", name="a", file_ids=["5.py", "6.py", "7.py", "8.py"])
        model = _model_with_subsystems(s_b, s_a)
        results = tracker.check_subsystem_coverage([], model)
        assert [r.subsystem_id for r in results] == ["s-a", "s-b"]
