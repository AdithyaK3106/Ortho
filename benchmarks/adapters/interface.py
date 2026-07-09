"""EngineeringSystemAdapter: the capability-based boundary every benchmark suite
calls through, and the executable spec a future second adapter (Claude Code,
Cursor, etc.) must satisfy.

Capability-based, not stage-based (GATE 2 decision): each method is phrased as
an engineering question a benchmark asks ("what symbols/imports/calls does
this repo have?", "what architecture is this?"), not a step in Ortho's
internal pipeline. A vendor with no separable "build_graphs" step can still
implement this interface by answering the same questions differently.

No abstract base beyond this one interface; no hypothetical vendor-specific
hooks added speculatively (YAGNI).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RepoIndex:
    """Result of scan_repository(): symbols, imports, calls, and scan stats."""

    symbols: list[str] = field(default_factory=list)          # qualified names
    imports: list[tuple[str, str]] = field(default_factory=list)  # (importer, imported)
    calls: list[tuple[str, str]] = field(default_factory=list)    # (caller, callee)
    files_total: int = 0
    files_scanned: int = 0
    parse_errors: list[str] = field(default_factory=list)


@dataclass
class ArchResult:
    """Result of detect_architecture(): style, layers, subsystems together."""

    style: str = "unknown"
    confidence: float = 0.0
    alternative: str | None = None
    alternative_confidence: float | None = None
    evidence: list[str] = field(default_factory=list)
    layers: dict[str, int] = field(default_factory=dict)         # file_id -> layer number
    subsystems: list[list[str]] = field(default_factory=list)    # list of file_id clusters


@dataclass
class RetrievalHit:
    """One ranked search result from retrieve()."""

    id: str
    content: str = ""
    relevance_score: float = 0.0
    file_id: str | None = None
    symbol_id: str | None = None


@dataclass
class ImpactResult:
    """Result of analyze_impact(): predicted-impacted files + risk score."""

    changed_file: str = ""
    impacted_files: list[str] = field(default_factory=list)
    blast_radius: int = 0
    risk_score: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class ContextResult:
    """Result of assemble_context(): token/latency/budget-fill metrics."""

    chunks_total: int = 0
    chunks_included: int = 0
    tokens_used: int = 0
    chars_included: int = 0
    latency_ms: float = 0.0
    budget_total: int = 0
    budget_fill_pct: float = 0.0


class EngineeringSystemAdapter(ABC):
    """Capability boundary: exactly 5 methods, each an engineering question."""

    @abstractmethod
    def scan_repository(self, repo_path: Path) -> RepoIndex:
        """What symbols, imports, and calls does this repo have?"""

    @abstractmethod
    def detect_architecture(self, repo_path: Path) -> ArchResult:
        """What architecture style, layers, and subsystems does this repo have?"""

    @abstractmethod
    def retrieve(self, repo_path: Path, query: str, k: int) -> list[RetrievalHit]:
        """What are the top-k most relevant results for this query in this repo?"""

    @abstractmethod
    def analyze_impact(self, repo_path: Path, changed_file: str) -> ImpactResult:
        """If this file changed, what else would be impacted?"""

    @abstractmethod
    def assemble_context(self, repo_path: Path, query: str, budget: int) -> ContextResult:
        """What context would be assembled for this query under this token budget?"""
