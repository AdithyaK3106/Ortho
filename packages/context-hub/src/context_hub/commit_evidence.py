"""Mine git_history commit messages as decision-engine evidence (task-025 part 2)."""

import re
import sqlite3
from dataclasses import dataclass

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _words(text: str) -> set[str]:
    """Lowercased word tokens. \\w with re.UNICODE (Python 3 default) covers
    non-ASCII scripts (CJK, Cyrillic, etc.) -- decision_engine._words uses
    [a-z0-9_] and is ASCII-only, which silently drops every non-English
    commit message; this module does not repeat that bug."""
    return set(_WORD_RE.findall(text.lower()))


@dataclass
class CommitEvidence:
    title: str
    description: str
    commit_hash: str
    author: str
    commit_date: str
    confidence: float
    source: str = "git_history"


def find_relevant_commits(
    db: sqlite3.Connection, repo_id: str, query: str, limit: int = 5
) -> list[CommitEvidence]:
    """Search git_history.message for words overlapping `query`.

    Jaccard overlap over lowercased word tokens (same approach as
    decision_engine._score_option's intent-fit calculation). Ties broken by
    most recent commit_date; note commit_date is only second-precision (see
    GitMetadataStore.load_git_history docstring), so among true ties the
    higher-rowid (later-inserted) row sorts first as a secondary tiebreak.

    Empty/whitespace-only query returns an empty list rather than "match
    everything" -- an empty query has no words to overlap with, so nothing
    can be meaningfully ranked as relevant.
    """
    query_words = _words(query)
    if not query_words:
        return []

    rows = db.execute(
        """
        SELECT commit_hash, author, commit_date, message, rowid
        FROM git_history
        WHERE repo_id = ?
        """,
        (repo_id,),
    ).fetchall()

    scored: list[tuple[float, str, CommitEvidence]] = []
    for commit_hash, author, commit_date, message, rowid in rows:
        message = message or ""
        msg_words = _words(message)
        if not msg_words:
            continue
        overlap = len(query_words & msg_words) / len(query_words)
        if overlap <= 0.0:
            continue

        first_line = message.splitlines()[0] if message else ""
        scored.append(
            (
                overlap,
                commit_date or "",
                CommitEvidence(
                    title=first_line,
                    description=message,
                    commit_hash=commit_hash,
                    author=author or "unknown",
                    commit_date=commit_date or "",
                    confidence=min(overlap, 1.0),
                ),
            )
        )

    # Sort by overlap desc, then commit_date desc (string ISO-8601 dates sort
    # lexicographically in chronological order); Python's sort is stable so
    # rows tied on both keys keep their original (rowid-ascending) query
    # order reversed by the final [:limit] slice is NOT what we want --
    # explicit reverse=True on the tuple keeps overlap and date both
    # descending without needing a third key.
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)

    return [evidence for _, _, evidence in scored[:limit]]
