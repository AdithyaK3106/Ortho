#!/usr/bin/env python
"""Test ortho on real repositories (fastapi, langchain, etc.)"""

import sys
import os

# Fix encoding on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from repo_intelligence.indexer import Indexer
from repo_intelligence.incremental_indexer import IncrementalIndexer

# Add repo-intelligence to path
repo_intelligence_path = Path(__file__).parent / "packages" / "repo-intelligence" / "src"
sys.path.insert(0, str(repo_intelligence_path))


def test_repo(repo_path: Path) -> dict:
    """Test scanning a real repository."""
    print(f"\n{'='*70}")
    print(f"Testing: {repo_path.name}")
    print(f"Path: {repo_path}")
    print(f"{'='*70}")

    if not repo_path.exists():
        print(f"✗ Repository not found: {repo_path}")
        return {"status": "NOT_FOUND", "repo": repo_path.name}

    try:
        # Check if git repo
        indexer = Indexer(repo_path)
        print(f"✓ Repository initialized for scanning")

        # Check git status
        incremental = IncrementalIndexer(repo_path)
        if incremental.is_git_repo():
            print(f"✓ Git repository detected")
        else:
            print(f"⚠ Not a git repository")

        # Scan repository
        print(f"\nScanning repository...")
        result = indexer.index_repository()

        print(f"\n{'─'*70}")
        print(f"SCAN RESULTS:")
        print(f"{'─'*70}")
        print(f"  Total files:       {result.total_files}")
        print(f"  Files scanned:     {result.files_scanned}")
        print(f"  Files with errors: {result.files_with_errors}")
        print(f"  Success rate:      {result.success_rate:.1f}%")
        print(f"  Symbols:           {result.total_symbols}")
        print(f"  Imports:           {result.total_imports}")
        print(f"  Calls:             {result.total_calls}")
        print(f"  Errors:            {result.error_count}")

        if result.error_count > 0:
            print(f"\n  Sample errors:")
            for error in result.errors[:3]:
                print(f"    - {error}")
            if len(result.errors) > 3:
                print(f"    ... and {len(result.errors) - 3} more")

        # Check acceptance
        accepted = indexer.can_accept_error_rate(result)
        print(f"\n  Acceptable error rate (≥90%): {'✓ YES' if accepted else '✗ NO'}")

        return {
            "status": "SUCCESS",
            "repo": repo_path.name,
            "total_files": result.total_files,
            "files_scanned": result.files_scanned,
            "symbols": result.total_symbols,
            "imports": result.total_imports,
            "calls": result.total_calls,
            "errors": result.error_count,
            "success_rate": result.success_rate,
            "accepted": accepted,
        }

    except Exception as e:
        print(f"✗ Error scanning repository: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "repo": repo_path.name, "error": str(e)}


def main():
    """Test all repositories in Repos/"""
    repos_dir = Path(__file__).parent / "Repos"

    print(f"\n{'#'*70}")
    print(f"# ORTHO REAL-REPO TEST SUITE")
    print(f"# Testing repositories in {repos_dir}")
    print(f"{'#'*70}")

    repos = ["fastapi", "langchain"]
    results = []

    for repo_name in repos:
        repo_path = repos_dir / repo_name
        result = test_repo(repo_path)
        results.append(result)

    # Summary
    print(f"\n\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")

    for result in results:
        status = result.get("status", "UNKNOWN")
        repo = result.get("repo", "unknown")

        if status == "SUCCESS":
            symbols = result.get("symbols", 0)
            imports = result.get("imports", 0)
            calls = result.get("calls", 0)
            success_rate = result.get("success_rate", 0)
            accepted = result.get("accepted", False)

            print(
                f"\n{repo:20s} | "
                f"Symbols: {symbols:5d} | "
                f"Imports: {imports:5d} | "
                f"Calls: {calls:5d} | "
                f"Success: {success_rate:5.1f}% | "
                f"Accepted: {'✓' if accepted else '✗'}"
            )
        elif status == "NOT_FOUND":
            print(f"\n{repo:20s} | ⚠ NOT FOUND")
        else:
            error = result.get("error", status)
            print(f"\n{repo:20s} | ✗ {error}")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
