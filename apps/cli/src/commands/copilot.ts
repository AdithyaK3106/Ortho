/**
 * ortho guardrails|decide|plan|refactor — Engineering copilot commands.
 * Bridges to copilot.py (real CliCommands: ArchitectureEnforcer,
 * DecisionEngine, FeaturePlanner, RefactoringAdvisor).
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const COPILOT_CLI = "apps/cli/src/commands/copilot.py";

/**
 * Run the bridge and map failures. A failed *report* (nonexistent path,
 * rejected intent) has already been printed to stdout by the Python side
 * before it exits 1 — re-printing the generic "exit code 1" rejection
 * would mislabel an expected failure report as a CLI crash, so only
 * spawn-level errors (missing python, etc.) get an "Error:" line.
 */
async function runCopilot(args: string[]): Promise<void> {
  try {
    await runPython(COPILOT_CLI, args);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (!/exit code \d+/.test(message)) {
      console.error("Error:", message);
    }
    process.exit(1);
  }
}

function requireIntent(intent: string, command: string): string {
  if (!intent || intent.trim().length === 0) {
    console.error(`Error: ${command} requires a non-empty intent.`);
    process.exit(1);
  }
  return intent;
}

export const guardrailsCommand = new Command()
  .command("guardrails [path]")
  .description("Check architecture violations (layer boundaries, cycles, module size)")
  .option("--severity <level>", "error or warning (default: all)")
  .action(async (path?: string, options?: { severity?: string }) => {
    if (options?.severity && !["error", "warning"].includes(options.severity)) {
      console.error(`Error: --severity must be 'error' or 'warning', got '${options.severity}'`);
      process.exit(1);
    }
    const args = ["guardrails", "--path", path || process.cwd()];
    if (options?.severity) args.push("--severity", options.severity);
    await runCopilot(args);
  });

export const decideCommand = new Command()
  .command("decide <intent>")
  .description("Decision support: change-impact + guardrail aggregation (intent = text or file path)")
  .option("--scan-path <dir>", "Directory to scan (default: current directory)")
  .option("--confidence <threshold>", "Minimum confidence 0.0–1.0")
  .action(async (intent: string, options?: { scanPath?: string; confidence?: string }) => {
    requireIntent(intent, "decide");
    if (options?.confidence) {
      const conf = parseFloat(options.confidence);
      if (isNaN(conf) || conf < 0.0 || conf > 1.0) {
        console.error(`Error: --confidence must be 0.0–1.0, got '${options.confidence}'`);
        process.exit(1);
      }
    }
    const args = ["decide", intent, "--scan-path", options?.scanPath || process.cwd()];
    if (options?.confidence) args.push("--confidence", options.confidence);
    await runCopilot(args);
  });

export const planCommand = new Command()
  .command("plan <intent>")
  .description("Feature planning: classified intent -> implementation paths")
  .option("--scan-path <dir>", "Directory to scan (default: current directory)")
  .action(async (intent: string, options: { scanPath?: string }) => {
    requireIntent(intent, "plan");
    await runCopilot(["plan", intent, "--scan-path", options.scanPath ?? process.cwd()]);
  });

export const refactorCommand = new Command()
  .command("refactor [path]")
  .description("Refactoring findings: bloat, tight coupling, circular dependencies")
  .action(async (path?: string) => {
    await runCopilot(["refactor", "--path", path ?? process.cwd()]);
  });
