"""Artifact ingestion validation contract."""

from dataclasses import dataclass
from typing import Optional


ARTIFACT_TYPES = {
    "frd",
    "adr",
    "architecture",
    "spec",
    "decision",
    "lesson_learned",
    "dev_note",
    "benchmark",
    "evidence",
    "workflow_run",
    "git_metadata",
    "project_memory",
}

RELEVANCE_SCOPES = {"global", "project", "module", "file"}


@dataclass
class ArtifactIngestionRequest:
    """Request to ingest an artifact into ContextHub."""

    type: str
    title: str
    content: str
    source: str
    relevance_scope: str
    tags: list[str]
    related_symbols: Optional[list[str]] = None


@dataclass
class ValidationResult:
    """Result of artifact ingestion validation."""

    is_valid: bool
    errors: list[str]


def validate_ingestion(req: ArtifactIngestionRequest) -> ValidationResult:
    """
    Validate artifact ingestion request. Reject invalid requests with detailed errors.

    No silent failures: all validation errors are enumerated.
    """
    errors = []

    # Type validation
    if not req.type:
        errors.append("type cannot be empty")
    elif req.type not in ARTIFACT_TYPES:
        errors.append(f"type must be one of: {', '.join(sorted(ARTIFACT_TYPES))}")

    # Title validation
    if not req.title:
        errors.append("title cannot be empty")
    elif len(req.title.strip()) == 0:
        errors.append("title cannot be whitespace only")

    # Content validation
    if not req.content:
        errors.append("content cannot be empty")
    elif len(req.content.strip()) == 0:
        errors.append("content cannot be whitespace only")

    # Source validation
    if not req.source:
        errors.append("source cannot be empty")
    elif len(req.source.strip()) == 0:
        errors.append("source cannot be whitespace only")

    # Relevance scope validation
    if not req.relevance_scope:
        errors.append("relevance_scope cannot be empty")
    elif req.relevance_scope not in RELEVANCE_SCOPES:
        errors.append(
            f"relevance_scope must be one of: {', '.join(sorted(RELEVANCE_SCOPES))}"
        )

    # Tags validation
    if not isinstance(req.tags, list):
        errors.append("tags must be a list")
    else:
        for i, tag in enumerate(req.tags):
            if not isinstance(tag, str):
                errors.append(f"tag at index {i} must be string, got {type(tag).__name__}")
            elif len(tag.strip()) == 0:
                errors.append(f"tag at index {i} cannot be whitespace only")

    # Related symbols validation (optional, deferred to Phase 2 when symbol registry available)
    if req.related_symbols is not None:
        if not isinstance(req.related_symbols, list):
            errors.append("related_symbols must be a list")
        else:
            for i, symbol_id in enumerate(req.related_symbols):
                if not isinstance(symbol_id, str):
                    errors.append(
                        f"related_symbols[{i}] must be string, got {type(symbol_id).__name__}"
                    )
                elif len(symbol_id.strip()) == 0:
                    errors.append(f"related_symbols[{i}] cannot be whitespace only")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
