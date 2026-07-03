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
  const pythonScript = path.join(__dirname, "../../python/scan_cli.py");

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
    const proc = spawn("python", [pythonScript, ...pythonArgs], {
      cwd,
      stdio: "inherit",
      shell: process.platform === "win32",
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
