import { runPython } from "./pybridge";

interface ScanOptions {
  watch?: boolean;
  verbose?: boolean;
  full?: boolean;
}

/**
 * ortho scan — Full repository scanning and indexing
 *
 * Discovers all Python files, extracts symbols, imports, and calls.
 * Supports watch mode for incremental re-indexing on file changes.
 *
 * Usage:
 *   ortho scan                    # Full repository scan
 *   ortho scan --watch            # Watch mode (re-index on changes)
 *   ortho scan --full             # Full re-index (ignore git state)
 *   ortho scan --verbose          # Verbose output
 */
export async function scanCommand(options: ScanOptions): Promise<void> {
  const pythonArgs = ["--repo-root", process.cwd()];

  if (options.watch) {
    pythonArgs.push("--watch");
  }

  if (options.full) {
    pythonArgs.push("--full");
  }

  if (options.verbose) {
    pythonArgs.push("--verbose");
  }

  return runPython(
    "packages/repo-intelligence/src/repo_intelligence/scan_cli.py",
    pythonArgs
  );
}
