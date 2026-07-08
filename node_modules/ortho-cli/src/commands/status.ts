/**
 * ortho status — Show current workflow state (reads .ortho/ortho.db directly).
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const WORKFLOW_CLI = "apps/cli/src/commands/workflow_cli.py";

export const statusCommand = new Command()
  .command("status")
  .description("Show current workflow state")
  .action(async () => {
    try {
      await runPython(WORKFLOW_CLI, ["--repo-root", process.cwd(), "status"]);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });
