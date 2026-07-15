"""CLI bridge for ortho memory search."""

import argparse
import sys
from pathlib import Path

# Spawned as a bare script by the TS CLI — add dependencies to path FIRST
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
for _p in (
    _PROJECT_ROOT / "packages" / "cli-commands" / "src",
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "context-hub" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _main():
    """Argparse entry point."""
    parser = argparse.ArgumentParser(description="Search workflow memory")
    parser.add_argument("query", help="Search keyword (e.g., guardrails, refactor, layer_boundaries)")
    parser.add_argument("--repo-path", default=".", help="Repository path (default: current directory)")
    args = parser.parse_args()

    from cli_commands.commands import CliCommands

    commands = CliCommands()
    report = commands.search_memory(args.repo_path, args.query)

    output = report.title + "\n\n" + report.content + "\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    _main()
