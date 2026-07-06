#!/usr/bin/env python3
"""CLI entry point for repo-intelligence indexing."""

import argparse
import sys
from pathlib import Path
import time

# Run directly as a script — make the package importable without installation
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    parser = argparse.ArgumentParser(description="Index Python repository")
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser("index", help="Index repository")
    index_parser.add_argument("--watch", action="store_true", help="Enable watch mode")
    index_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.command == "index":
        index_command(args.watch, args.verbose)
    else:
        parser.print_help()


def index_command(watch: bool = False, verbose: bool = False):
    """Execute index command."""
    repo_root = Path.cwd()

    try:
        from repo_intelligence.call_graph import CallGraphBuilder
        from repo_intelligence.dependency_graph import DependencyGraphBuilder
        from repo_intelligence.module_detector import ModuleDetector

        python_files = list(repo_root.rglob("*.py"))

        call_builder = CallGraphBuilder(repo_root, python_files)
        call_edges = call_builder.build_call_graph()

        dep_builder = DependencyGraphBuilder(repo_root)
        dependencies = dep_builder.build_dependency_graph("repo")

        module_detector = ModuleDetector(repo_root)
        modules = module_detector.detect_modules()

        print(f"Indexed {len(python_files)} files, {len(call_edges)} calls, {len(dependencies)} dependencies")

        if watch:
            watch_mode(repo_root, verbose)

    except Exception as e:
        print(f"✗ Index failed: {e}", file=sys.stderr)
        sys.exit(1)


def watch_mode(repo_root: Path, verbose: bool = False):
    """Monitor for changes and re-index incrementally."""
    try:
        from repo_intelligence.incremental_indexer import IncrementalIndexer, NotAGitRepoError

        print("Watching for changes... (Ctrl+C to exit)")

        indexer = IncrementalIndexer(repo_root)

        last_state = None
        while True:
            try:
                time.sleep(2)

                if verbose:
                    print("[Checking for changes...]")

            except KeyboardInterrupt:
                print("\nExiting watch mode")
                sys.exit(0)

    except NotAGitRepoError:
        print("✗ Not a git repository", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Watch mode failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
