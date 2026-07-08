/**
 * ortho history — List past workflow runs for this repository.
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const WORKFLOW_CLI = "apps/cli/src/commands/workflow_cli.py";

export const historyCommand = new Command()
  .command("history")
  .description("List past workflow runs or show details for specific run")
  .option("--limit <n>", "Maximum runs to list", "10")
  .action(async (options: { limit: string }) => {
    try {
      await runPython(WORKFLOW_CLI, [
        "--repo-root", process.cwd(),
        "history",
        "--limit", options.limit,
      ]);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });
