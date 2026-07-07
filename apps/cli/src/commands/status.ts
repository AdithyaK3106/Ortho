/**
 * ortho status — Show current workflow state
 */

import { Command } from "commander";
import fetch from "node-fetch";

export const statusCommand = new Command()
  .command("status")
  .description("Show current workflow state")
  .action(async () => {
    try {
      const response = await fetch("http://localhost:17234/api/status", {
        method: "GET",
      });

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status} ${response.statusText}`
        );
      }

      const result = await response.json();

      if (!result.workflow_run) {
        console.log("No active workflow.");
        return;
      }

      const run = result.workflow_run;
      console.log(`Run ID: ${run.id}`);
      console.log(`Intent: ${run.intent_class}`);
      console.log(`Status: ${run.status}`);
      console.log(`Started: ${run.started_at}`);

      if (run.status === "awaiting_approval") {
        console.log("\n⏸️  Awaiting approval at approval gate.");
        console.log("Next step: Use `ortho approve` or `ortho reject <reason>`");
      } else if (run.status === "complete") {
        console.log(`Completed: ${run.completed_at}`);
        console.log(`Evidence artifacts: ${run.evidence.length}`);
      } else if (run.status === "failed" || run.status === "rejected") {
        console.log(`Failed: ${run.completed_at}`);
      }

      if (run.steps) {
        console.log(`\nProgress: ${run.steps.filter((s: any) => s.status === "complete").length}/${run.steps.length} steps`);
      }
    } catch (error) {
      console.error(
        "Error:",
        error instanceof Error ? error.message : String(error)
      );
      process.exit(1);
    }
  });
