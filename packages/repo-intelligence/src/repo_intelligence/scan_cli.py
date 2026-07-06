"""CLI entry point for ortho scan command."""

import argparse
import sys
import logging
from pathlib import Path

from repo_intelligence.indexer import Indexer
from repo_intelligence.incremental_indexer import IncrementalIndexer


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


def format_summary(result) -> str:
    """Format indexing result as human-readable summary."""
    return (
        f"\n✓ Scan complete:\n"
        f"  Files: {result.files_scanned}/{result.total_files}\n"
        f"  Symbols: {result.total_symbols}\n"
        f"  Imports: {result.total_imports}\n"
        f"  Calls: {result.total_calls}\n"
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
        indexer = Indexer(repo_root)

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
        return 0

    except Exception as e:
        print(f"✗ Scan error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
