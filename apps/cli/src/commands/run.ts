/**
 * ortho run "<intent>" — Main orchestration entry point
 * Classifies intent, selects agents/skills, builds plan, optionally executes
 */

import { Command } from "commander";
import fetch from "node-fetch";

interface RunOptions {
  dryRun?: boolean;
}

export const runCommand = new Command()
  .command("run <intent>")
  .description("Execute orchestration workflow for intent")
  .option(
    "--dry-run",
    "Show execution plan without running (default: false)"
  )
  .action(async (intent: string, options: RunOptions) => {
    try {
      const response = await fetch("http://localhost:17234/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          intent,
          dryRun: options.dryRun || false,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status} ${response.statusText}`
        );
      }

      const result = await response.json();

      if (options.dryRun) {
        console.log("📋 Execution Plan (dry-run):");
        console.log(`Intent: ${result.plan.intent_class}`);
        console.log(`Steps: ${result.plan.steps.length}`);
        console.log(`Tokens: ${result.plan.total_estimated_tokens}`);
        console.log(`Approval required: ${result.plan.human_approval_required}`);

        console.log("\nSteps:");
        result.plan.steps.forEach((step: any, idx: number) => {
          const gate = step.approval_gate ? " [🔐 APPROVAL]" : "";
          console.log(
            `  ${idx + 1}. ${step.agent_name} (${step.skill_names.join(", ")})${gate}`
          );
        });
      } else {
        console.log("✅ Workflow started");
        console.log(`Run ID: ${result.workflow_run.id}`);
        console.log(`Status: ${result.workflow_run.status}`);

        if (result.workflow_run.status === "awaiting_approval") {
          console.log(
            "\n⏸️  Workflow paused at approval gate. Use `ortho approve` or `ortho reject`."
          );
        } else if (result.workflow_run.status === "complete") {
          console.log("\n✅ Workflow complete.");
          console.log(
            `Evidence: ${result.workflow_run.evidence.length} artifacts`
          );
        } else if (result.workflow_run.status === "failed") {
          console.log("\n❌ Workflow failed.");
          console.log(`Error: ${result.workflow_run.evidence[0]?.error_message}`);
        }
      }
    } catch (error) {
      console.error(
        "Error:",
        error instanceof Error ? error.message : String(error)
      );
      process.exit(1);
    }
  });
