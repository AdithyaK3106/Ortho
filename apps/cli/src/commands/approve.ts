/**
 * ortho approve [--reason "<text>"] — Approve pending approval gate
 */

import { Command } from "commander";
import fetch from "node-fetch";

interface ApproveOptions {
  reason?: string;
}

export const approveCommand = new Command()
  .command("approve")
  .description("Approve pending approval gate and resume workflow")
  .option("--reason <text>", "Optional reason for approval")
  .action(async (options: ApproveOptions) => {
    try {
      const response = await fetch("http://localhost:17234/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: options.reason || "Approved by user",
        }),
      });

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status} ${response.statusText}`
        );
      }

      const result = await response.json();

      console.log("✅ Approval granted.");
      console.log(`Status: ${result.workflow_run.status}`);

      if (result.workflow_run.status === "complete") {
        console.log("Workflow complete.");
      } else if (result.workflow_run.status === "awaiting_approval") {
        console.log(
          "Next approval gate: use `ortho approve` or `ortho reject`"
        );
      }
    } catch (error) {
      console.error(
        "Error:",
        error instanceof Error ? error.message : String(error)
      );
      process.exit(1);
    }
  });
