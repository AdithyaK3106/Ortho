"""CLI entry point for ortho scan command."""

import argparse
import sys
import logging
from pathlib import Path

# Spawned as a bare script by the TS CLI — never depend on install state
# (ARCHITECT mandate, task-011; same idiom as arch-intelligence graph_utils).
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
for _p in (_PROJECT_ROOT / "shared" / "storage" / "src",
           _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
           _PROJECT_ROOT / "packages" / "context-hub" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from storage import OrthoDatabase

from repo_intelligence.indexer import Indexer, IndexResult
from repo_intelligence.incremental_indexer import IncrementalIndexer
from repo_intelligence.index_store import IndexStore, mint_repo_id, _mint
from repo_intelligence.file_discoverer import FileDiscoverer
from context_hub import GitMetadataStore


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output."""
    # Windows consoles default to cp1252, which can't encode '✓'/'✗' and made a
    # successful scan exit 1 while printing its summary.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stdout,
    )


def format_summary(result: IndexResult) -> str:
    """Format indexing result as human-readable summary."""
    return (
        f"\n✓ Scan complete:\n"
        f"  Files: {result.files_scanned}/{result.total_files}\n"
        f"  Symbols: {result.total_symbols}\n"
        f"  Imports: {result.total_imports}\n"
        f"  Calls: {result.total_calls}\n"
        f"  Persisted: {result.persisted_symbols} symbols, "
        f"{result.persisted_imports} imports, "
        f"{result.persisted_calls} calls "
        f"({result.persisted_calls_dropped} dropped unresolved)\n"
        f"  Success rate: {result.success_rate:.1f}%"
    )


def main() -> int:
    """Main entry point for ortho scan."""
    parser = argparse.ArgumentParser(
        description='Scan and index Python repository',
        prog='ortho scan',
    )
    parser.add_argument(
        '--repo-root',
        type=str,
        default='.',
        help='Repository root directory (default: current directory)',
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Enable watch mode (re-index on file changes)',
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full re-index (ignore git state)',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output',
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    repo_root = Path(args.repo_root).resolve()

    if not repo_root.exists():
        print(f"✗ Repository not found: {repo_root}", file=sys.stderr)
        return 1

    try:
        # Persist to .ortho/ortho.db (task-011): migrate schema, then scan+store
        db = OrthoDatabase(repo_root)
        db.migrate()
        store = IndexStore(db, mint_repo_id(repo_root), repo_root)
        store.ensure_repository(name=repo_root.name)

        indexer = Indexer(repo_root, store=store)

        if args.watch:
            # Watch mode
            try:
                indexer.watch()
                return 0
            except KeyboardInterrupt:
                return 0
            except ImportError as e:
                print(f"✗ Watch mode unavailable: {e}", file=sys.stderr)
                return 1

        # Standard scan mode
        result = indexer.index_repository()

        # Check success rate
        if not indexer.can_accept_error_rate(result):
            print(format_summary(result), file=sys.stderr)
            print(
                f"✗ Error rate too high ({100 - result.success_rate:.1f}%)",
                file=sys.stderr,
            )
            return 1

        print(format_summary(result))

        _load_git_history(db, store.repo_id, repo_root, args.verbose)

        return 0

    except Exception as e:
        print(f"✗ Scan error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def _load_git_history(db: OrthoDatabase, repo_id: str, repo_root: Path, verbose: bool) -> None:
    """Populate git_history for every scanned file (task-025 part 1).

    Best-effort: GitMetadataStore already treats a missing/non-git repo as a
    silent no-op per file, so failures here must never fail the scan itself —
    a git-history gap is strictly less severe than losing the symbol index.
    """
    try:
        conn = db.connection()
        try:
            git_store = GitMetadataStore(conn, repo_root, repo_id)
            if git_store.git_repo is None:
                return
            for file_path in FileDiscoverer(repo_root).find_python_files():
                rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
                file_id = _mint(repo_id, rel_path)
                git_store.load_git_history(file_id, rel_path)
        finally:
            conn.close()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Git history load skipped: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    sys.exit(main())
