import { runPython } from "./pybridge";

export interface IndexOptions {
  watch?: boolean;
  verbose?: boolean;
}

export async function indexCommand(options: IndexOptions): Promise<void> {
  const args = ["--repo-root", process.cwd()];

  if (options.watch) {
    args.push("--watch");
  }

  if (options.verbose) {
    args.push("--verbose");
  }

  // "index" is an alias for scan — reuse the same entry point.
  return runPython(
    "packages/repo-intelligence/src/repo_intelligence/scan_cli.py",
    args
  );
}
