/**
 * ortho reject <reason> — Reject current approval gate (terminal state).
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const WORKFLOW_CLI = "apps/cli/src/commands/workflow_cli.py";

export const rejectCommand = new Command()
  .command("reject <reason>")
  .description("Reject current approval gate and mark workflow as failed")
  .option("--run-id <id>", "Specific workflow run to reject (default: latest awaiting)")
  .action(async (reason: string, options: { runId?: string }) => {
    const args = ["--repo-root", process.cwd(), "reject", reason];
    if (options.runId) args.push("--run-id", options.runId);
    try {
      await runPython(WORKFLOW_CLI, args);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });
