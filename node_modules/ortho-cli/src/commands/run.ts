/**
 * ortho run "<intent>" — Main orchestration entry point.
 * Spawns workflow_cli.py (classify intent, build plan, execute with gates).
 * Previously pointed at an HTTP API on :17234 that no server implemented.
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const WORKFLOW_CLI = "apps/cli/src/commands/workflow_cli.py";

export const runCommand = new Command()
  .command("run <intent>")
  .description("Execute orchestration workflow for intent")
  .option("--dry-run", "Show execution plan without running")
  .option("--yes", "Auto-approve all approval gates")
  .action(async (intent: string, options: { dryRun?: boolean; yes?: boolean }) => {
    const args = ["--repo-root", process.cwd(), "run", intent];
    if (options.dryRun) args.push("--dry-run");
    if (options.yes) args.push("--yes");
    try {
      await runPython(WORKFLOW_CLI, args);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });
