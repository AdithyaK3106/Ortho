/**
 * Shared helpers for CLI commands that spawn Ortho's Python entry points.
 *
 * Path resolution uses require.main.filename (the compiled dist/index.js),
 * so it is independent of the caller's cwd — commands work from any directory.
 */

import { spawn } from "child_process";
import * as path from "path";

/** Ortho repo root, resolved from the CLI entry point (apps/cli/dist/index.js). */
export function orthoRoot(): string {
  const entryPoint = require.main?.filename || __filename;
  return path.resolve(path.dirname(entryPoint), "../../..");
}

/**
 * Spawn a Python script with inherited stdio. Tries `python`, falls back to
 * `python3` (macOS/Linux often ship only python3). Rejects on non-zero exit.
 */
export function runPython(scriptRelPath: string, args: string[]): Promise<void> {
  const script = path.resolve(orthoRoot(), scriptRelPath);

  const trySpawn = (cmd: string, allowFallback: boolean): Promise<void> =>
    new Promise((resolve, reject) => {
      const proc = spawn(cmd, [script, ...args], {
        cwd: process.cwd(),
        stdio: "inherit",
      });
      proc.on("error", (err: NodeJS.ErrnoException) => {
        if (err.code === "ENOENT" && allowFallback) {
          trySpawn("python3", false).then(resolve, reject);
        } else {
          reject(new Error(`Failed to spawn ${cmd}: ${err.message}`));
        }
      });
      proc.on("exit", (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Command failed with exit code ${code}`));
        }
      });
    });

  return trySpawn("python", true);
}

/**
 * Spawn a Python script capturing stdout (stderr passes through).
 * Same python → python3 fallback. Resolves with stdout on exit 0.
 */
export function runPythonCapture(scriptRelPath: string, args: string[]): Promise<string> {
  const script = path.resolve(orthoRoot(), scriptRelPath);

  const trySpawn = (cmd: string, allowFallback: boolean): Promise<string> =>
    new Promise((resolve, reject) => {
      const proc = spawn(cmd, [script, ...args], {
        cwd: process.cwd(),
        stdio: ["ignore", "pipe", "inherit"],
      });
      let output = "";
      proc.stdout!.on("data", (data: Buffer) => {
        output += data.toString();
      });
      proc.on("error", (err: NodeJS.ErrnoException) => {
        if (err.code === "ENOENT" && allowFallback) {
          trySpawn("python3", false).then(resolve, reject);
        } else {
          reject(new Error(`Failed to spawn ${cmd}: ${err.message}`));
        }
      });
      proc.on("exit", (code) => {
        if (code === 0) {
          resolve(output);
        } else {
          reject(new Error(`Command failed with exit code ${code}`));
        }
      });
    });

  return trySpawn("python", true);
}
