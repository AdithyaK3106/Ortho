import { spawn } from "child_process";
import { join } from "path";

export interface IndexOptions {
  watch?: boolean;
  verbose?: boolean;
}

export async function indexCommand(options: IndexOptions): Promise<void> {
  const projectRoot = process.cwd();

  const args = ["index"];

  if (options.watch) {
    args.push("--watch");
  }

  if (options.verbose) {
    args.push("--verbose");
  }

  const pythonScript = join(__dirname, "../../../packages/repo-intelligence/cli.py");

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
