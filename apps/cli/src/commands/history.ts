/**
 * ortho history [--id <run-id>] [--limit N] — List or show workflow runs
 */

import { Command } from "commander";
import fetch from "node-fetch";

interface HistoryOptions {
  id?: string;
  limit?: string;
}

export const historyCommand = new Command()
  .command("history")
  .description("List past workflow runs or show details for specific run")
  .option("--id <id>", "Show details for specific run")
  .option("--limit <n>", "Number of runs to list (default: 10)", "10")
  .action(async (options: HistoryOptions) => {
    try {
      const params = new URLSearchParams();
      if (options.id) {
        params.append("id", options.id);
      } else {
        params.append("limit", options.limit);
      }

      const response = await fetch(
        `http://localhost:17234/api/history?${params.toString()}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) {
        throw new Error(
          `API error: ${response.status} ${response.statusText}`
        );
      }

      const result = await response.json();

      if (options.id) {
        // Show details for specific run
        const run = result.workflow_run;
        console.log(`Run ID: ${run.id}`);
        console.log(`Intent: ${run.intent_class}`);
        console.log(`Status: ${run.status}`);
        console.log(`Started: ${run.started_at}`);
        if (run.completed_at) {
          console.log(`Completed: ${run.completed_at}`);
        }

        if (run.steps && run.steps.length > 0) {
          console.log(`\nSteps:`);
          run.steps.forEach((step: any, idx: number) => {
            const gate = step.approval_gate ? " [🔐]" : "";
            console.log(
              `  ${idx + 1}. ${step.agent_name}${gate} — ${step.status}`
            );
          });
        }

        if (run.evidence && run.evidence.length > 0) {
          console.log(`\nEvidence (${run.evidence.length} artifacts):`);
          run.evidence.slice(0, 5).forEach((ev: any) => {
            console.log(
              `  • ${ev.step_name} (${ev.evidence_type}): ${ev.status}`
            );
          });
          if (run.evidence.length > 5) {
            console.log(
              `  ... and ${run.evidence.length - 5} more artifacts`
            );
          }
        }
      } else {
        // List runs
        console.log("Recent workflow runs:");
        if (
          !result.runs ||
          result.runs.length === 0
        ) {
          console.log("  (none)");
        } else {
          result.runs.forEach((run: any, idx: number) => {
            const statusIcon =
              run.status === "complete"
                ? "✅"
                : run.status === "failed" || run.status === "rejected"
                  ? "❌"
                  : "⏳";
            console.log(
              `  ${idx + 1}. [${run.id.slice(0, 8)}] ${run.intent_class} ${statusIcon} (${run.status})`
            );
            console.log(`     Started: ${run.started_at}`);
          });
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
