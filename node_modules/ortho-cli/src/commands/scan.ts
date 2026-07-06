import { spawn } from "child_process";
import * as path from "path";

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
  const cwd = process.cwd();
  // Works from both src/commands (ts-node) and dist/commands (tsc output):
  // both are 4 levels below the repo root.
  const pythonScript = path.join(
    __dirname,
    "../../../../packages/repo-intelligence/src/repo_intelligence/scan_cli.py"
  );

  // Build Python command arguments
  const pythonArgs = ["--repo-root", cwd];

  if (options.watch) {
    pythonArgs.push("--watch");
  }

  if (options.full) {
    pythonArgs.push("--full");
  }

  if (options.verbose) {
    pythonArgs.push("--verbose");
  }

  // Run Python script
  return new Promise((resolve, reject) => {
    // No shell: spawn with an args array is injection-safe and works for
    // python.exe on Windows without one.
    const proc = spawn("python", [pythonScript, ...pythonArgs], {
      cwd,
      stdio: "inherit",
    });

    proc.on("error", (err) => {
      reject(new Error(`Failed to spawn Python: ${err.message}`));
    });

    proc.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Scan failed with exit code ${code}`));
      }
    });
  });
}
