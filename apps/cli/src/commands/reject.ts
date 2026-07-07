/**
 * ortho reject "<reason>" — Reject current approval gate
 */

import { Command } from "commander";
import fetch from "node-fetch";

export const rejectCommand = new Command()
  .command("reject <reason>")
  .description("Reject current approval gate and mark workflow as failed")
  .action(async (reason: string) => {
    try {
      const response = await fetch("http://localhost:17234/api/reject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status} ${response.statusText}`
        );
      }

      const result = await response.json();

      console.log("❌ Workflow rejected.");
      console.log(`Status: ${result.workflow_run.status}`);
      console.log(`Reason: ${reason}`);

      if (result.workflow_run.completed_at) {
        console.log(`Completed: ${result.workflow_run.completed_at}`);
      }
    } catch (error) {
      console.error(
        "Error:",
        error instanceof Error ? error.message : String(error)
      );
      process.exit(1);
    }
  });
