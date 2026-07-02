"""Data types for impact analysis and debt scoring components."""

from dataclasses import dataclass, field


@dataclass
class Symbol:
    """Code symbol (function, class, method, etc.)."""
    id: str
    name: str
    file_id: str
    start_line: int = 0
    end_line: int = 0


@dataclass
class CallEdge:
    """Call relationship between symbols."""
    caller_id: str
    callee_id: str
    confidence: float = 0.8


@dataclass
class ImportEdge:
    """Import relationship between files."""
    importer_file_id: str
    imported_file_id: str | None = None
    imported_module: str = ""
    is_external: bool = False


@dataclass
class GitFileMetadata:
    """Git metadata for a file."""
    file_path: str
    commits_30d: int = 0
    size_bytes: int = 0


@dataclass
class ImpactReport:
    """Report on change impact analysis results."""

    changed_file_id: str
    direct_dependents: list[str] = field(default_factory=list)
    transitive_dependents: list[str] = field(default_factory=list)
    risk_score: float = 0.0
    analysis_confidence: float = 1.0
    blast_radius: int = 0
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate score ranges."""
        assert 0.0 <= self.risk_score <= 1.0, f"risk_score must be 0.0–1.0, got {self.risk_score}"
        assert 0.0 <= self.analysis_confidence <= 1.0, f"analysis_confidence must be 0.0–1.0, got {self.analysis_confidence}"
        assert self.blast_radius >= 0, f"blast_radius must be non-negative, got {self.blast_radius}"


@dataclass
class DebtScore:
    """Technical debt score for a module (5 dimensions)."""

    module_id: str
    total_score: float = 0.0
    coupling_score: float = 0.0
    churn_score: float = 0.0
    complexity_score: float = 0.0
    test_coverage_score: float = 0.0
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate score ranges."""
        for score_name in ['total_score', 'coupling_score', 'churn_score', 'complexity_score', 'test_coverage_score']:
            score = getattr(self, score_name)
            assert 0.0 <= score <= 1.0, f"{score_name} must be 0.0–1.0, got {score}"


@dataclass
class DependencyHealthReport:
    """Dependency health analysis for a module."""

    module_id: str
    fan_in: int = 0
    fan_out: int = 0
    high_fan_in: bool = False
    high_fan_out: bool = False
    is_hub: bool = False
    cycles_involved: list[list[str]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate fields."""
        assert self.fan_in >= 0, f"fan_in must be non-negative, got {self.fan_in}"
        assert self.fan_out >= 0, f"fan_out must be non-negative, got {self.fan_out}"
