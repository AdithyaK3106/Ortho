/**
 * ortho context add|search — Context hub artifact store and search.
 * Bridges to context.py (ArtifactStore + BM25 search over .ortho/ortho.db).
 */

import { Command } from "commander";
import { runPython } from "./pybridge";

const CONTEXT_CLI = "apps/cli/src/commands/context.py";

export const contextCommand = new Command()
  .command("context")
  .description("Context hub: add and search artifacts");

contextCommand
  .command("add")
  .description("Add an artifact to the context hub")
  .requiredOption("--title <title>", "Artifact title")
  .requiredOption("--content <content>", "Artifact content")
  .option("--type <type>", "Artifact type (default: dev_note)")
  .option("--source <source>", "Artifact source (default: manual)")
  .option("--tags <tags>", "Comma-separated tags")
  .action(async (options: {
    title: string; content: string; type?: string; source?: string; tags?: string;
  }) => {
    const args = ["--repo-root", process.cwd(), "add",
      "--title", options.title, "--content", options.content];
    if (options.type) args.push("--type", options.type);
    if (options.source) args.push("--source", options.source);
    if (options.tags) args.push("--tags", options.tags);
    try {
      await runPython(CONTEXT_CLI, args);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

contextCommand
  .command("search <query>")
  .description("Search context hub artifacts (BM25)")
  .option("--limit <n>", "Result limit", "10")
  .option("--type <type>", "Filter by artifact type")
  .action(async (query: string, options: { limit: string; type?: string }) => {
    const args = ["--repo-root", process.cwd(), "search", query, "--limit", options.limit];
    if (options.type) args.push("--type", options.type);
    try {
      await runPython(CONTEXT_CLI, args);
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });
