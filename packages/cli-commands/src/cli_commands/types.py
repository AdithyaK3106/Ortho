from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CliReport:
    title: str
    content: str
    format: str = "text"
    success: bool = True
    violations: Optional[Any] = None  # list[GuardrailViolation] | None
    recommendations: Optional[Any] = None  # list[Recommendation] | None
    search_results: Optional[Any] = None  # list[WorkflowRunResult] | None
