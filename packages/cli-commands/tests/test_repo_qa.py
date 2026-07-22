"""Repository Understanding Q&A: real match, honest no-match, and
adversarial cases -- never fabricate an answer, per the roadmap's
"Answers should be generated from... NOT simple vector search" and the
same evidence-gating discipline used elsewhere (ArchStyle.UNKNOWN,
LayerDetector's evidence requirement)."""

from dataclasses import dataclass

import pytest

from cli_commands.repo_qa import answer_question


@dataclass
class _FakeSymbol:
    name: str


class _FakeGraphQueries:
    """Minimal duck-typed stand-in for RepoGraphQueries, real behavior."""

    def __init__(self, importers_by_file=None, callers_by_symbol=None):
        self._importers_by_file = importers_by_file or {}
        self._callers_by_symbol = callers_by_symbol or {}

    def find_importers(self, file_path, include_type=False):
        return self._importers_by_file.get(file_path, [])

    def find_callers(self, symbol, depth=1):
        return self._callers_by_symbol.get(symbol, [])


class TestRealMatch:
    def test_matches_module_by_path_with_real_evidence(self):
        file_to_module = {"/repo/src/auth.py": "src.auth"}
        symbols_by_file = {"/repo/src/auth.py": [_FakeSymbol("login")]}
        gq = _FakeGraphQueries(
            importers_by_file={"/repo/src/auth.py": ["/repo/src/app.py"]},
        )
        file_to_module["/repo/src/app.py"] = "src.app"

        result = answer_question("how does auth work", file_to_module, symbols_by_file, gq)

        assert result.answered is True
        assert result.keyword == "auth"
        assert "/repo/src/auth.py" in result.matched_files
        assert any("src.auth" in e for e in result.evidence)
        assert any("imported by: src.app" in e for e in result.evidence)

    def test_matches_symbol_name_and_reports_callers(self):
        file_to_module = {"/repo/src/billing.py": "src.billing"}
        symbols_by_file = {"/repo/src/billing.py": [_FakeSymbol("charge_card")]}
        gq = _FakeGraphQueries(callers_by_symbol={"charge_card": ["checkout_flow"]})

        result = answer_question("explain charge_card", file_to_module, symbols_by_file, gq)

        assert result.answered is True
        assert any("charge_card() called by: checkout_flow" in e for e in result.evidence)

    def test_falls_back_to_shorter_word_when_longest_word_has_no_match(self):
        """Regression: "how does application context work" previously
        extracted only "application" (11 chars, beats "context" at 7) and
        answered from that alone -- on a real repo with no "application"
        symbol but a real AppContext class, the answer was near-empty even
        though "context" would have matched plenty. The longest candidate
        with no matches must fall back to the next-longest, not give up."""
        file_to_module = {"/repo/src/ctx.py": "src.ctx"}
        symbols_by_file = {"/repo/src/ctx.py": [_FakeSymbol("AppContext")]}
        gq = _FakeGraphQueries()

        result = answer_question(
            "how does application context work", file_to_module, symbols_by_file, gq
        )

        assert result.answered is True
        assert result.keyword == "context"
        assert "/repo/src/ctx.py" in result.matched_files

    def test_prefers_the_candidate_with_more_matches_not_just_the_first_hit(self):
        """Regression, exact real-repo case: "how does application context
        work in this codebase" on Flask. "application" (11 chars) is tried
        before "context" (7 chars) and finds one incidental match
        (test_session_using_application_root), which a first-match-wins
        fallback would accept and stop there -- even though "context"
        matches many real, relevant symbols (AppContext,
        teardown_appcontext, etc.) in the same repo. The candidate with
        the most matches must win, not merely the first one with any."""
        file_to_module = {
            "/repo/tests/test_basic.py": "tests.test_basic",
            "/repo/src/ctx.py": "src.ctx",
            "/repo/src/app.py": "src.app",
        }
        symbols_by_file = {
            "/repo/tests/test_basic.py": [_FakeSymbol("test_session_using_application_root")],
            "/repo/src/ctx.py": [_FakeSymbol("AppContext")],
            "/repo/src/app.py": [_FakeSymbol("teardown_appcontext")],
        }
        gq = _FakeGraphQueries()

        result = answer_question(
            "how does application context work in this codebase",
            file_to_module,
            symbols_by_file,
            gq,
        )

        assert result.answered is True
        assert result.keyword == "context"
        assert "/repo/src/ctx.py" in result.matched_files
        assert "/repo/src/app.py" in result.matched_files

    def test_evidence_resolves_importers_to_module_names_not_raw_paths(self):
        """Regression: find_importers returns raw file paths, not module
        names -- evidence must resolve through file_to_module, not leak
        an unresolved path into the answer."""
        file_to_module = {
            "/repo/src/widget.py": "src.widget",
            "/repo/src/consumer.py": "src.consumer",
        }
        symbols_by_file = {"/repo/src/widget.py": []}
        gq = _FakeGraphQueries(importers_by_file={"/repo/src/widget.py": ["/repo/src/consumer.py"]})

        result = answer_question("about widget", file_to_module, symbols_by_file, gq)

        joined = "\n".join(result.evidence)
        assert "src.consumer" in joined
        assert "/repo/src/consumer.py" not in joined


class TestHonestNoMatch:
    def test_no_match_reports_no_evidence_found_not_a_guess(self):
        file_to_module = {"/repo/src/foo.py": "src.foo"}
        symbols_by_file = {"/repo/src/foo.py": []}
        gq = _FakeGraphQueries()

        result = answer_question("how does xyzzyplugh work", file_to_module, symbols_by_file, gq)

        assert result.answered is False
        assert result.keyword == "xyzzyplugh"

    def test_stopwords_only_extracts_no_keyword(self):
        """A question with no real subject ('how does it work') must not
        silently pick a meaningless 2-letter word and search for it."""
        file_to_module = {"/repo/src/init.py": "src.init"}
        symbols_by_file = {"/repo/src/init.py": []}
        gq = _FakeGraphQueries()

        result = answer_question("how does it work", file_to_module, symbols_by_file, gq)

        assert result.answered is False
        assert result.keyword is None


class TestAdversarialCases:
    def test_empty_question_returns_unanswered_not_raise(self):
        result = answer_question("", {}, {}, _FakeGraphQueries())
        assert result.answered is False

    def test_whitespace_only_question_returns_unanswered(self):
        result = answer_question("   ", {}, {}, _FakeGraphQueries())
        assert result.answered is False

    def test_matches_are_capped_not_dumping_whole_repo(self):
        """A too-generic keyword matching most of the repo must be capped,
        not returned as an unbounded list."""
        file_to_module = {f"/repo/src/service_{i}.py": f"src.service_{i}" for i in range(50)}
        symbols_by_file = {k: [] for k in file_to_module}
        gq = _FakeGraphQueries()

        result = answer_question("about service", file_to_module, symbols_by_file, gq)

        assert result.answered is True
        assert len(result.matched_files) <= 8
        assert any("more matches" in e or "more files matched" in e for e in result.evidence)

    def test_empty_repo_returns_unanswered_not_raise(self):
        result = answer_question("how does auth work", {}, {}, _FakeGraphQueries())
        assert result.answered is False

    def test_question_with_no_extractable_word_handled_gracefully(self):
        result = answer_question("???---!!!", {"/repo/a.py": "a"}, {"/repo/a.py": []}, _FakeGraphQueries())
        assert result.answered is False
        assert result.keyword is None
