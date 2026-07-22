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

export const reviewCommand = new Command()
  .command("review [path]")
  .description("Unified review: architecture violations + decision summary, one scan")
  .option("--severity <level>", "error or warning (default: all)")
  .action(async (path?: string, options?: { severity?: string }) => {
    if (options?.severity && !["error", "warning"].includes(options.severity)) {
      console.error(`Error: --severity must be 'error' or 'warning', got '${options.severity}'`);
      process.exit(1);
    }
    const args = ["review", "--path", path || process.cwd()];
    if (options?.severity) args.push("--severity", options.severity);
    await runCopilot(args);
  });

export const guardrailsCommand = new Command()
  .command("guardrails [path]")
  .description("Check architecture violations (layer boundaries, cycles, module size)")
  .option("--severity <level>", "error or warning (default: all)")
  .option("--against-branch <name>", "Restrict violations to files changed vs. this local branch")
  .action(async (path?: string, options?: { severity?: string; againstBranch?: string }) => {
    if (options?.severity && !["error", "warning"].includes(options.severity)) {
      console.error(`Error: --severity must be 'error' or 'warning', got '${options.severity}'`);
      process.exit(1);
    }
    const args = ["guardrails", "--path", path || process.cwd()];
    if (options?.severity) args.push("--severity", options.severity);
    if (options?.againstBranch) args.push("--against-branch", options.againstBranch);
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

export const feedbackCommand = new Command()
  .command("feedback <decision> <findingKey>")
  .description(
    'Record accept/reject on a finding ("{rule_id} {location}" from guardrails/decide/review output) -- future runs cite the decision and reason instead of just "seen before"'
  )
  .option("--path <dir>", "Repository path (default: current directory)")
  .option("--reason <text>", "Why (shown on future runs if rejected)")
  .action(async (decision: string, findingKey: string, options?: { path?: string; reason?: string }) => {
    if (decision !== "accept" && decision !== "reject") {
      console.error(`Error: decision must be 'accept' or 'reject', got '${decision}'`);
      process.exit(1);
    }
    requireIntent(findingKey, "feedback");
    const args = ["feedback", decision, findingKey, "--path", options?.path || process.cwd()];
    if (options?.reason) args.push("--reason", options.reason);
    await runCopilot(args);
  });

export const askCommand = new Command()
  .command("ask <question>")
  .description(
    "Repository Understanding: structural Q&A grounded in the real call/import graph (e.g. \"how does auth work\") -- not vector search, answers only from real graph evidence"
  )
  .option("--scan-path <dir>", "Directory to scan (default: current directory)")
  .action(async (question: string, options?: { scanPath?: string }) => {
    requireIntent(question, "ask");
    await runCopilot(["ask", question, "--scan-path", options?.scanPath || process.cwd()]);
  });

export const orchestrateCommand = new Command()
  .command("orchestrate <intent>")
  .description(
    "Chain plan+decide+review into one composed report for an intent. Does not write code, approve, or merge -- that's the developer's / LLM's job; Ortho advises."
  )
  .option("--scan-path <dir>", "Directory to scan (default: current directory)")
  .action(async (intent: string, options?: { scanPath?: string }) => {
    requireIntent(intent, "orchestrate");
    await runCopilot(["orchestrate", intent, "--scan-path", options?.scanPath || process.cwd()]);
  });

export const crossRepoCommand = new Command()
  .command("cross-repo <paths...>")
  .description(
    "Shared/reusable code across 2-5 real repos, via real AST-structural similarity -- not naming-based guesswork"
  )
  .option("--threshold <value>", "Similarity threshold 0.0-1.0 (default: 0.7)")
  .action(async (paths: string[], options?: { threshold?: string }) => {
    if (paths.length < 2) {
      console.error(`Error: cross-repo needs at least 2 repo paths, got ${paths.length}`);
      process.exit(1);
    }
    if (options?.threshold) {
      const t = parseFloat(options.threshold);
      if (isNaN(t) || t < 0.0 || t > 1.0) {
        console.error(`Error: --threshold must be 0.0–1.0, got '${options.threshold}'`);
        process.exit(1);
      }
    }
    const args = ["cross-repo", ...paths];
    if (options?.threshold) args.push("--threshold", options.threshold);
    await runCopilot(args);
  });

export const memoryCommand = new Command()
  .command("memory <query>")
  .description("Search workflow_run artifacts in ContextHub (learned from past guardrails/decide/plan/refactor runs)")
  .option("--repo-path <dir>", "Repository path (default: current directory)")
  .action(async (query: string, options?: { repoPath?: string }) => {
    requireIntent(query, "memory");
    const args = [query, "--repo-path", options?.repoPath || process.cwd()];
    await runPython("apps/cli/src/commands/memory_search.py", args);
  });
