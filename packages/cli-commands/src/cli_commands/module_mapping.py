"""Shared file-path -> module-identifier resolution.

Used consistently by every adapter in the guardrails/decide pipeline that
needs to map a real file path to a module name, so all adapters agree on
the same identifier for the same file.
"""

from __future__ import annotations

from pathlib import Path


def path_to_module(file_path: Path, repo_root: Path) -> str:
    """Convert a file path to a dotted module string relative to repo_root."""
    try:
        rel = file_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        rel = Path(file_path.name)

    parts = rel.with_suffix("").parts
    parts = tuple(p for p in parts if p != "__init__")
    if not parts:
        return rel.stem
    return ".".join(parts)
