"""CLI bridge for the four engineering-copilot commands.

ortho guardrails/decide/plan/refactor -> CliCommands (packages/cli-commands).
Mirrors context.py's bridge pattern: sys.path bootstrap, argparse _main(),
spawned by copilot.ts via pybridge.ts.

--path/--scan-path are required at this level: the TS side always passes
an explicit directory (defaulting to the user's cwd), keeping the
no-unbounded-scan discipline from tasks 017/019 mechanical.
"""

import sys
from pathlib import Path

# Spawned as a bare script by the TS CLI — add dependencies to path FIRST
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
for _pkg in (
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
    _PROJECT_ROOT / "packages" / "arch-intelligence" / "src",
    _PROJECT_ROOT / "packages" / "impact-analysis" / "src",
    _PROJECT_ROOT / "packages" / "change-planner" / "src",
    _PROJECT_ROOT / "packages" / "feature-planner" / "src",
    _PROJECT_ROOT / "packages" / "refactoring-advisor" / "src",
    _PROJECT_ROOT / "packages" / "arch-guardrails" / "src",
    _PROJECT_ROOT / "packages" / "decision-engine" / "src",
    _PROJECT_ROOT / "packages" / "context-hub" / "src",
    _PROJECT_ROOT / "packages" / "cli-commands" / "src",
):
    if str(_pkg) not in sys.path:
        sys.path.insert(0, str(_pkg))


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="ortho engineering copilot")
    subparsers = parser.add_subparsers(dest="action", required=True)

    guardrails_parser = subparsers.add_parser("guardrails", help="Architecture violation check")
    guardrails_parser.add_argument("--path", required=True, help="Directory to scan")

    decide_parser = subparsers.add_parser("decide", help="Decision support")
    decide_parser.add_argument("intent", help="Free-text intent or a file path")
    decide_parser.add_argument("--scan-path", required=True, help="Directory to scan")

    plan_parser = subparsers.add_parser("plan", help="Feature implementation paths")
    plan_parser.add_argument("intent", help="Free-text feature intent")
    plan_parser.add_argument("--scan-path", required=True, help="Directory to scan")

    refactor_parser = subparsers.add_parser("refactor", help="Refactoring findings")
    refactor_parser.add_argument("--path", required=True, help="Directory to scan")

    args = parser.parse_args()

    from cli_commands.commands import CliCommands

    commands = CliCommands()
    if args.action == "guardrails":
        report = commands.guardrails(args.path)
    elif args.action == "decide":
        report = commands.decide(args.intent, scan_path=args.scan_path)
    elif args.action == "plan":
        report = commands.plan(args.intent, scan_path=args.scan_path)
    else:
        report = commands.refactor(args.path)

    # Windows console encoding: use binary mode to bypass cp1252 codec
    # and write UTF-8 bytes directly to stdout (which is inherited from the
    # TS layer and goes to the real terminal/pipe).
    output = report.title + "\n\n" + report.content + "\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.stdout.buffer.flush()
    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    _main()
