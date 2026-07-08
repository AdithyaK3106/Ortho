/**
 * ortho approve — Approve pending approval gate and resume workflow.
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const WORKFLOW_CLI = "apps/cli/src/commands/workflow_cli.py";

export const approveCommand = new Command()
  .command("approve")
  .description("Approve pending approval gate and resume workflow")
  .option("--run-id <id>", "Specific workflow run to approve (default: latest awaiting)")
  .action(async (options: { runId?: string }) => {
    const args = ["--repo-root", process.cwd(), "approve"];
    if (options.runId) args.push("--run-id", options.runId);
    try {
      await runPython(WORKFLOW_CLI, args);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });
