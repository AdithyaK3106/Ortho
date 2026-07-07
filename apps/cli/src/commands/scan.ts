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

  // BUG-001 FIX: Use require.main.filename to find entry point instead of __dirname
  // This ensures path resolution works regardless of where CLI is run from.
  // When compiled, __dirname points to dist/ but require.main.filename points to the entry point (index.js)
  const entryPoint = require.main?.filename || __filename;
  const entryDir = path.dirname(entryPoint);

  // Calculate repo root: entry point is in apps/cli/dist/index.js
  // So we need to go up 4 levels: dist -> cli -> apps -> ortho-root
  const repoRoot = path.resolve(entryDir, "../../..");

  const pythonScript = path.resolve(
    repoRoot,
    "packages/repo-intelligence/src/repo_intelligence/scan_cli.py"
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
