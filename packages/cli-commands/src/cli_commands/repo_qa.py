"""Repository Understanding: answer structural questions from real graph data.

Deliberately NOT an NL-understanding pipeline and NOT vector search (per the
product vision: "Answers should be generated from: repository graph, call
graph, dependency graph, architecture graph. NOT simple vector search.").
The approach is mechanical and honest about its limits:

1. Extract a plain keyword from the question (strip stopwords/punctuation).
2. Case-insensitive substring match against real file paths, module names,
   and symbol names already produced by the scan -- no semantic guessing.
3. For matched files, report real call/import graph facts: what calls into
   them, what they import, what imports them.
4. No match -> say so plainly. This is not a chatbot that always has an
   answer; an unanswerable question gets "no evidence found", matching the
   same evidence-gating discipline as ArchStyle.UNKNOWN and the redesigned
   LayerDetector elsewhere in this codebase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from repo_intelligence.symbol_extractor import Symbol


class _GraphQueries(Protocol):
    """Structural type for RepoGraphQueries -- avoids a hard runtime
    dependency on repo_intelligence from this module (see module
    docstring), while still giving mypy --strict something real to check
    call sites against."""

    def find_importers(self, file_path: str, include_type: bool = False) -> list[str]: ...
    def find_callers(self, symbol: str, depth: int = 1) -> list[str]: ...

# Common question words stripped before matching -- keeps "how does auth
# work" from trying to match a file literally named "how.py". Deliberately
# small and generic (English question-formation words), not a stopword list
# tuned to any particular vocabulary.
_STOPWORDS = frozenset({
    "how", "does", "do", "what", "is", "are", "the", "a", "an", "where",
    "when", "why", "explain", "work", "works", "implemented", "flow",
    "to", "of", "in", "on", "for", "and", "or", "this", "that", "which",
    "it", "its", "it's", "they", "them", "their", "we", "us", "our",
    "you", "your", "i", "my", "me", "he", "she", "his", "her",
})

# A question matching an implausibly large fraction of the repo isn't a
# useful answer -- it means the keyword was too generic (e.g. "the", "get").
# Capped rather than dumping every match.
_MAX_MATCHED_FILES = 8
_MAX_CALLERS_SHOWN = 5
_MAX_IMPORTERS_SHOWN = 5


@dataclass
class QAResult:
    question: str
    keyword: str | None
    matched_files: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    answered: bool = False


def _extract_keyword(question: str) -> str | None:
    """Pull the most specific real word out of a question. Picks the
    longest non-stopword token -- a cheap, honest heuristic (no NLU), since
    the longest word in a question like "how does auth work" is usually
    the actual subject ("auth")."""
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", question.lower())
    # len >= 3: a 2-char token is too generic to be a meaningful subject and
    # will almost always false-positive as a substring inside unrelated
    # longer identifiers (e.g. "it" inside "init", "commit", "unit").
    candidates = [t for t in tokens if t not in _STOPWORDS and len(t) >= 3]
    if not candidates:
        return None
    longest: str = max(candidates, key=len)
    return longest


def answer_question(
    question: str,
    file_to_module: dict[str, str],
    symbols_by_file: dict[str, list["Symbol"]],
    graph_queries: _GraphQueries,
) -> QAResult:
    """Answer a structural question about the repo using real scan data.

    graph_queries is a RepoGraphQueries instance (structurally typed via
    _GraphQueries above to avoid a hard runtime dependency on
    repo_intelligence from this module).
    """
    if not question or not question.strip():
        return QAResult(question=question, keyword=None, answered=False)

    keyword = _extract_keyword(question)
    if keyword is None:
        return QAResult(question=question, keyword=None, answered=False)

    matched_files: list[str] = []
    match_reasons: dict[str, str] = {}
    for file_path, module in file_to_module.items():
        if keyword in module.lower() or keyword in file_path.lower():
            matched_files.append(file_path)
            match_reasons[file_path] = f"module/path contains '{keyword}'"
            continue
        for symbol in symbols_by_file.get(file_path, []):
            if keyword in symbol.name.lower():
                matched_files.append(file_path)
                match_reasons[file_path] = f"defines symbol '{symbol.name}' matching '{keyword}'"
                break

    if not matched_files:
        return QAResult(question=question, keyword=keyword, answered=False)

    matched_files = matched_files[:_MAX_MATCHED_FILES]
    truncated = len(matched_files) == _MAX_MATCHED_FILES

    evidence: list[str] = []
    for file_path in matched_files:
        module = file_to_module.get(file_path, file_path)
        evidence.append(f"{module}: {match_reasons[file_path]}")

        importers = graph_queries.find_importers(file_path)
        if importers:
            # find_importers returns raw file paths, not module names --
            # resolve through file_to_module so evidence reads consistently
            # with the module names used everywhere else in the answer.
            importer_modules = [file_to_module.get(i, i) for i in importers]
            shown = importer_modules[:_MAX_IMPORTERS_SHOWN]
            more = f" (+{len(importer_modules) - len(shown)} more)" if len(importer_modules) > len(shown) else ""
            evidence.append(f"  imported by: {', '.join(shown)}{more}")

        for symbol in symbols_by_file.get(file_path, []):
            if keyword in symbol.name.lower():
                callers = graph_queries.find_callers(symbol.name, depth=1)
                if callers:
                    shown = callers[:_MAX_CALLERS_SHOWN]
                    more = f" (+{len(callers) - len(shown)} more)" if len(callers) > len(shown) else ""
                    evidence.append(f"  {symbol.name}() called by: {', '.join(shown)}{more}")

    if truncated:
        evidence.append(f"(showing first {_MAX_MATCHED_FILES} matches; more files matched '{keyword}')")

    return QAResult(
        question=question,
        keyword=keyword,
        matched_files=matched_files,
        evidence=evidence,
        answered=True,
    )
