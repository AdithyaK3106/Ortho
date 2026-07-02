"""ADR awareness: cross-reference ADR markdown against the repo tree (stateless).

Extraction contract fully specified in
.ases/tasks/task-010-adr-awareness-reporting/spec.md ("ADR Path Extraction Contract"),
decision rationale in ADR-009.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from .types import ArchitectureModel

_STATUS_RE = re.compile(r"^\**Status:?\**\s*[:]?\s*([A-Z][A-Z \-]*)", re.MULTILINE)
_TITLE_RE = re.compile(r"^#\s*(ADR-\d+)\s*:?\s*(.*)$", re.MULTILINE)

# Rule 1/2: "File:" / "Code:" lines (optionally bulleted), value up to end of line
_FILE_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:File|Code):\s*(.+)$", re.MULTILINE)

# Rule 3: markdown links [text](path)
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# Rule 4: backtick-quoted spans
_BACKTICK_RE = re.compile(r"`([^`]+)`")

_URL_PREFIXES = ("http://", "https://", "ftp://")
# A real file extension needs >=1 non-dot, non-digit-only stem char before it
# (rejects bare `.db`, and numeric-looking spans like `0.7`)
_EXT_RE = re.compile(r"^[A-Za-z_][\w\-]*\.[a-zA-Z]{1,5}$")
_GLOB_CHARS = set("*?[]")
_EXTERNAL_REPO_RE = re.compile(r"(github\.com|gitlab\.com)")
_BARE_OWNER_REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")


@dataclass
class ADRStatus:
    """Cross-reference result for a single ADR file."""

    adr_id: str
    title: str
    status: str
    referenced_paths: list[str] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)
    classification: str = "UNKNOWN"
    evidence: list[str] = field(default_factory=list)


# Subsystems with more files than this are flagged if no ADR references any of their files.
# Heuristic hint, not a hard rule — see plan.md Task 2.
_SUBSYSTEM_COVERAGE_MIN_FILES = 3


@dataclass
class SubsystemADRCoverage:
    """Whether a detected subsystem has at least one owning ADR reference (heuristic hint)."""

    subsystem_id: str
    subsystem_name: str
    file_count: int
    has_owning_adr: bool
    owning_adr_ids: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def _looks_like_path(candidate: str) -> bool:
    """A candidate is path-shaped if it has no whitespace and contains '/' or a file extension."""
    if not candidate or any(ch.isspace() for ch in candidate):
        return False
    return "/" in candidate or bool(_EXT_RE.search(candidate))


def _is_unsupported(candidate: str) -> bool:
    """Glob patterns, URLs, external repo refs — recognized but excluded entirely."""
    if any(ch in _GLOB_CHARS for ch in candidate):
        return True
    if candidate.startswith(_URL_PREFIXES):
        return True
    if _EXTERNAL_REPO_RE.search(candidate):
        return True
    # Bare "owner/repo" GitHub shorthand: exactly one '/', last segment has no file extension
    if candidate.count("/") == 1 and _BARE_OWNER_REPO_RE.match(candidate):
        last_segment = candidate.rsplit("/", 1)[-1]
        if not _EXT_RE.match(last_segment):
            return True
    return False


def _normalize_path(raw: str) -> str | None:
    """Trim, normalize separators, strip leading './' and leading '/'. None if malformed/empty."""
    candidate = raw.strip().strip("`")
    if not candidate or "\x00" in candidate:
        return None
    candidate = candidate.replace("\\", "/")
    if candidate.startswith("./"):
        candidate = candidate[2:]
    while candidate.startswith("/"):
        candidate = candidate[1:]
    candidate = candidate.strip()
    return candidate or None


def _extract_candidates(text: str) -> list[str]:
    """Run all four extraction rules in precedence order, return raw (un-normalized) candidates."""
    candidates: list[str] = []

    for m in _FILE_LINE_RE.finditer(text):
        value = m.group(1).strip().strip("`").strip()
        if value:
            candidates.append(value)

    for m in _MD_LINK_RE.finditer(text):
        target = m.group(1).strip()
        if target.startswith("#"):
            continue
        candidates.append(target)

    for m in _BACKTICK_RE.finditer(text):
        candidates.append(m.group(1).strip())

    return candidates


def _extract_referenced_paths(text: str) -> list[str]:
    """Extract, filter, normalize, and deduplicate path references per the extraction contract."""
    seen: dict[str, None] = {}
    for raw in _extract_candidates(text):
        if not _looks_like_path(raw):
            continue
        if _is_unsupported(raw):
            continue
        normalized = _normalize_path(raw)
        if normalized is None:
            continue
        seen.setdefault(normalized, None)
    return list(seen.keys())


def _parse_status(text: str) -> str:
    m = _STATUS_RE.search(text)
    if not m:
        return "UNKNOWN"
    value = m.group(1).strip()
    for known in ("ACCEPTED", "PROPOSED", "DRAFT", "SUPERSEDED"):
        if value.startswith(known):
            return known
    return "UNKNOWN"


def _parse_title(text: str, adr_id: str) -> str:
    m = _TITLE_RE.search(text)
    if m and m.group(1) == adr_id:
        return m.group(2).strip()
    return ""


class ADRTracker:
    """Cross-references ADRs against the current repo tree (stateless)."""

    def check_adrs(self, adr_dir: Path, repo_root: Path) -> list[ADRStatus]:
        """See spec.md Component 1 for the full contract and edge cases."""
        adr_dir = Path(adr_dir)
        repo_root = Path(repo_root)

        if not adr_dir.is_dir():
            return []

        results: list[ADRStatus] = []
        for adr_file in sorted(adr_dir.glob("ADR-*.md")):
            adr_id = adr_file.stem.split("-", 2)
            adr_id = "-".join(adr_id[:2]) if len(adr_id) >= 2 else adr_file.stem

            try:
                text = adr_file.read_text(encoding="utf-8")
            except OSError:
                results.append(
                    ADRStatus(
                        adr_id=adr_id,
                        title="",
                        status="UNKNOWN",
                        classification="UNKNOWN",
                        evidence=[f"Could not read {adr_file}"],
                    )
                )
                continue

            status = _parse_status(text)
            title = _parse_title(text, adr_id)
            referenced_paths = _extract_referenced_paths(text)

            missing_paths = [
                p for p in referenced_paths if not (repo_root / p).exists()
            ]

            if not referenced_paths:
                classification = "UNLINKED"
                evidence = ["No code references found in ADR text"]
            elif missing_paths:
                classification = "STALE"
                evidence = [f"Missing referenced path: {p}" for p in missing_paths]
            else:
                classification = "OK"
                evidence = [f"All {len(referenced_paths)} referenced path(s) exist"]

            results.append(
                ADRStatus(
                    adr_id=adr_id,
                    title=title,
                    status=status,
                    referenced_paths=referenced_paths,
                    missing_paths=missing_paths,
                    classification=classification,
                    evidence=evidence,
                )
            )

        results.sort(key=lambda r: r.adr_id)
        return results

    def check_subsystem_coverage(
        self,
        adr_statuses: list[ADRStatus],
        architecture_model: ArchitectureModel,
    ) -> list[SubsystemADRCoverage]:
        """
        For each subsystem with more than _SUBSYSTEM_COVERAGE_MIN_FILES files, flag whether
        any ADR's referenced_paths overlaps the subsystem's file_ids. Heuristic hint only —
        does not affect check_adrs()'s OK/STALE/UNLINKED/UNKNOWN classification (plan.md Task 2:
        "reported as a hint, not a hard failure").

        Args:
            adr_statuses: output of check_adrs() (or any list of ADRStatus)
            architecture_model: task-008's ArchitectureModel (layers/subsystems)

        Returns:
            One SubsystemADRCoverage per subsystem with file_count > _SUBSYSTEM_COVERAGE_MIN_FILES,
            sorted by subsystem_id. Subsystems at or below the threshold are omitted entirely.
        """
        results: list[SubsystemADRCoverage] = []

        for subsystem in architecture_model.subsystems:
            file_count = len(subsystem.file_ids)
            if file_count <= _SUBSYSTEM_COVERAGE_MIN_FILES:
                continue

            subsystem_files = set(subsystem.file_ids)
            owning_adr_ids = [
                status.adr_id
                for status in adr_statuses
                if subsystem_files & set(status.referenced_paths)
            ]

            has_owning_adr = bool(owning_adr_ids)
            if has_owning_adr:
                evidence = [
                    f"Referenced by {', '.join(owning_adr_ids)}",
                ]
            else:
                evidence = [
                    f"Subsystem has {file_count} files (> {_SUBSYSTEM_COVERAGE_MIN_FILES}) "
                    "but no ADR references any of them",
                ]

            results.append(
                SubsystemADRCoverage(
                    subsystem_id=subsystem.id,
                    subsystem_name=subsystem.name,
                    file_count=file_count,
                    has_owning_adr=has_owning_adr,
                    owning_adr_ids=owning_adr_ids,
                    evidence=evidence,
                )
            )

        results.sort(key=lambda r: r.subsystem_id)
        return results
