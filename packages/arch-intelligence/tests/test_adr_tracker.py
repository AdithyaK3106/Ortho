"""ADRTracker tests — fixture-based, repository-independent per spec.md."""

from pathlib import Path

import pytest

from arch_intelligence.adr_tracker import ADRTracker


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
