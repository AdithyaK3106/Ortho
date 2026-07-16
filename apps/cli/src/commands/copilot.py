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

    review_parser = subparsers.add_parser("review", help="Unified guardrails + decision summary")
    review_parser.add_argument("--path", required=True, help="Directory to scan")
    review_parser.add_argument("--severity", choices=["error", "warning"], help="Filter violations by severity")

    guardrails_parser = subparsers.add_parser("guardrails", help="Architecture violation check")
    guardrails_parser.add_argument("--path", required=True, help="Directory to scan")
    guardrails_parser.add_argument("--severity", choices=["error", "warning"], help="Filter violations by severity")

    decide_parser = subparsers.add_parser("decide", help="Decision support")
    decide_parser.add_argument("intent", help="Free-text intent or a file path")
    decide_parser.add_argument("--scan-path", required=True, help="Directory to scan")
    decide_parser.add_argument("--confidence", help="Minimum confidence threshold (0.0-1.0)")

    plan_parser = subparsers.add_parser("plan", help="Feature implementation paths")
    plan_parser.add_argument("intent", help="Free-text feature intent")
    plan_parser.add_argument("--scan-path", required=True, help="Directory to scan")

    refactor_parser = subparsers.add_parser("refactor", help="Refactoring findings")
    refactor_parser.add_argument("--path", required=True, help="Directory to scan")

    feedback_parser = subparsers.add_parser("feedback", help="Record accept/reject on a finding")
    feedback_parser.add_argument("decision", choices=["accept", "reject"], help="accept or reject")
    feedback_parser.add_argument("finding_key", help='"{rule_id} {location}" as shown in guardrails/decide/review output')
    feedback_parser.add_argument("--path", required=True, help="Repository path")
    feedback_parser.add_argument("--reason", default="", help="Why (shown on future runs if rejected)")

    ask_parser = subparsers.add_parser("ask", help="Repository Understanding: structural Q&A")
    ask_parser.add_argument("question", help="Question, e.g. 'how does auth work'")
    ask_parser.add_argument("--scan-path", required=True, help="Directory to scan")

    orchestrate_parser = subparsers.add_parser("orchestrate", help="Chain plan+decide+review into one report")
    orchestrate_parser.add_argument("intent", help="Free-text intent")
    orchestrate_parser.add_argument("--scan-path", required=True, help="Directory to scan")

    cross_repo_parser = subparsers.add_parser("cross-repo", help="Shared/reusable code across 2-5 real repos")
    cross_repo_parser.add_argument("paths", nargs="+", help="2-5 repository paths to compare")
    cross_repo_parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold 0.0-1.0")

    args = parser.parse_args()

    from cli_commands.commands import CliCommands

    commands = CliCommands()
    if args.action == "review":
        kwargs = {}
        if hasattr(args, "severity") and args.severity:
            kwargs["severity_filter"] = args.severity
        report = commands.review(args.path, **kwargs)
    elif args.action == "guardrails":
        kwargs = {}
        if hasattr(args, "severity") and args.severity:
            kwargs["severity_filter"] = args.severity
        report = commands.guardrails(args.path, **kwargs)
    elif args.action == "decide":
        kwargs = {"scan_path": args.scan_path}
        if hasattr(args, "confidence") and args.confidence:
            try:
                conf = float(args.confidence)
            except ValueError:
                parser.error(f"--confidence must be a float, got '{args.confidence}'")
            if not (0.0 <= conf <= 1.0):
                parser.error(f"--confidence must be 0.0–1.0, got {conf}")
            kwargs["confidence_threshold"] = conf
        report = commands.decide(args.intent, **kwargs)
    elif args.action == "plan":
        report = commands.plan(args.intent, scan_path=args.scan_path)
    elif args.action == "feedback":
        report = commands.feedback(args.path, args.finding_key, args.decision, args.reason)
    elif args.action == "ask":
        report = commands.ask(args.scan_path, args.question, scan_path=args.scan_path)
    elif args.action == "orchestrate":
        report = commands.orchestrate(args.intent, scan_path=args.scan_path)
    elif args.action == "cross-repo":
        report = commands.cross_repo(args.paths, threshold=args.threshold)
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
