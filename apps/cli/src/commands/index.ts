import { spawn } from "child_process";
import { join } from "path";

export interface IndexOptions {
  watch?: boolean;
  verbose?: boolean;
}

export async function indexCommand(options: IndexOptions): Promise<void> {
  const projectRoot = process.cwd();

  const args = ["--repo-root", projectRoot];

  if (options.watch) {
    args.push("--watch");
  }

  if (options.verbose) {
    args.push("--verbose");
  }

  // "index" is an alias for scan — reuse the same entry point. Works from both
  // src/commands and dist/commands (both are 4 levels below the repo root).
  const pythonScript = join(
    __dirname,
    "../../../../packages/repo-intelligence/src/repo_intelligence/scan_cli.py"
  );

  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python", [pythonScript, ...args], {
      cwd: projectRoot,
      stdio: "inherit",
    });

    pythonProcess.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Index command failed with exit code ${code}`));
      }
    });

    pythonProcess.on("error", (error) => {
      reject(error);
    });

    if (options.watch) {
      process.on("SIGINT", () => {
        pythonProcess.kill("SIGINT");
        resolve();
      });
    }
  });
}
