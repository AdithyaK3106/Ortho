"""Cross-Repository Intelligence: real structural code reuse across 2+ repos.

Reuses arch_intelligence.reuse_detector.ReuseDetector's AST-structural
similarity algorithm (already correct and tested for within-repo use) by
pooling symbols/sources from multiple repo scans, tagging each entry with
its source repo, and reporting only clusters that span more than one repo.
Same-repo-only clusters are not cross-repo evidence and are dropped.

Never fabricates "shared patterns" from naming alone -- two symbols named
"validate" prove nothing by themselves. Only real AST-structural similarity
(tree-sitter node-type-sequence comparison) counts as evidence, matching
this codebase's evidence discipline elsewhere (arch-guardrails,
refactoring-advisor).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arch_intelligence.reuse_detector import ReuseCluster, ReuseDetector
from repo_intelligence.symbol_extractor import Symbol

_MIN_REPOS = 2
_MAX_REPOS = 5
# ReuseDetector.find_similar is O(n^2) within each bucket of same-type,
# similar-sized symbols -- observed directly (not theoretical) to take
# ~11 minutes comparing click+typer (a combined ~4,000 symbols), versus
# ~52s scoped to single subdirectories. Fail fast with actionable guidance
# rather than let a pilot user's terminal hang for minutes with no feedback.
_MAX_POOLED_SYMBOLS = 2000


@dataclass
class CrossRepoMatch:
    repos: list[str]
    symbol_ids: list[str]
    similarity: float
    evidence: list[str] = field(default_factory=list)


def _repo_of(file_key: str, repo_roots: dict[str, str]) -> str:
    """Which repo (by the name the caller gave it) does this file belong to."""
    for root, name in repo_roots.items():
        if file_key.startswith(root):
            return name
    return "?"


def find_cross_repo_reuse(
    repo_paths: list[str],
    threshold: float = 0.7,
) -> list[CrossRepoMatch]:
    """Scan each repo_path, pool their symbols under repo-tagged keys, and
    return only ReuseDetector clusters that span 2+ distinct repos.

    Raises ValueError if fewer than 2 or more than 5 repo paths are given --
    "cross-repo" is meaningless for one repo, and comparing more than a
    handful of large real repos at once (each symbol pair is a similarity
    comparison) is a real, observed performance cliff, not a theoretical one.
    """
    if len(repo_paths) < _MIN_REPOS:
        raise ValueError(f"cross-repo comparison needs at least {_MIN_REPOS} repos, got {len(repo_paths)}")
    if len(repo_paths) > _MAX_REPOS:
        raise ValueError(f"cross-repo comparison supports at most {_MAX_REPOS} repos at once, got {len(repo_paths)}")

    from cli_commands.repo_scanner import scan_repository

    repo_roots: dict[str, str] = {}
    pooled_symbols: dict[str, list[Symbol]] = {}
    pooled_sources: dict[str, str] = {}

    for repo_path in repo_paths:
        repo_name = Path(repo_path).name
        scan = scan_repository(repo_path)
        repo_roots[str(scan.repo_root)] = repo_name

        for file_key, symbols in scan.symbols_by_file.items():
            if not symbols:
                continue
            try:
                source = Path(file_key).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            # Tag the file key with its repo so cluster membership can be
            # traced back to a specific repo even if two repos happen to
            # have files at the same relative path.
            tagged_key = f"{repo_name}::{file_key}"
            pooled_symbols[tagged_key] = symbols
            pooled_sources[tagged_key] = source

    total_symbols = sum(len(s) for s in pooled_symbols.values())
    if total_symbols > _MAX_POOLED_SYMBOLS:
        raise ValueError(
            f"cross-repo comparison would pool {total_symbols} symbols across "
            f"{len(repo_paths)} repos (limit {_MAX_POOLED_SYMBOLS}) -- the "
            "underlying similarity algorithm is O(n^2) and this would likely "
            "take minutes. Scope the comparison to specific subdirectories "
            "instead of whole repos, e.g. pass a package's src/ path rather "
            "than its repo root."
        )

    clusters = ReuseDetector().find_similar(pooled_symbols, pooled_sources, threshold=threshold)

    matches: list[CrossRepoMatch] = []
    for cluster in clusters:
        cluster_repos = sorted({_tagged_repo(fid) for fid in cluster.file_ids})
        if len(cluster_repos) < 2:
            continue  # same-repo-only cluster -- not cross-repo evidence
        matches.append(CrossRepoMatch(
            repos=cluster_repos,
            symbol_ids=cluster.symbol_ids,
            similarity=cluster.similarity,
            evidence=cluster.evidence,
        ))

    matches.sort(key=lambda m: -m.similarity)
    return matches


def _tagged_repo(tagged_file_id: str) -> str:
    return tagged_file_id.split("::", 1)[0]
