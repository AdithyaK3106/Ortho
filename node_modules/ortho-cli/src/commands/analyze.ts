import { Command } from "commander";
import { runPythonCapture } from "./pybridge";

export const analyzeCommand = new Command()
  .name("analyze")
  .description("Full architecture analysis")
  .option("--impact <file>", "Change impact analysis for a file")
  .option("--depth <n>", "Impact traversal depth (default 3)")
  .option("--adr-check", "Cross-reference ADRs against the repo tree")
  .option("--reuse", "Find structurally similar symbols")
  .option("--threshold <n>", "Reuse similarity threshold (default 0.7)")
  .option("--format <format>", "Output format: text or json", "text")
  .action(async (options): Promise<void> => {
    const pythonArgs = ["--repo-root", process.cwd()];
    if (options.impact) {
      pythonArgs.push("--impact", options.impact);
    }
    if (options.depth) {
      pythonArgs.push("--depth", options.depth);
    }
    if (options.adrCheck) {
      pythonArgs.push("--adr-check");
    }
    if (options.reuse) {
      pythonArgs.push("--reuse");
    }
    if (options.threshold) {
      pythonArgs.push("--threshold", options.threshold);
    }

    const output = await runPythonCapture(
      "apps/cli/src/commands/analyze.py",
      pythonArgs
    ).catch((error) => {
      console.error("Error:", error instanceof Error ? error.message : String(error));
      process.exit(1);
    });

    let result: any;
    try {
      result = JSON.parse(output);
    } catch {
      console.log(output);
      return;
    }

    if (options.format === "json") {
      console.log(JSON.stringify(result));
      return;
    }

    if (options.adrCheck) {
      const adrs = result.adrs ?? [];
      if (adrs.length === 0) {
        console.log("No ADRs found under .ases/architecture/adrs/.");
      }
      for (const adr of adrs) {
        console.log(`${adr.adr_id} | ${adr.status} | ${adr.classification}`);
        for (const missing of adr.missing_paths ?? []) {
          console.log(`  missing: ${missing}`);
        }
      }
    } else if (options.reuse) {
      const clusters = result.clusters ?? [];
      if (clusters.length === 0) {
        console.log("No reuse clusters above the similarity threshold.");
      }
      for (const cluster of clusters) {
        console.log(`similarity ${cluster.similarity.toFixed(2)}: ${cluster.symbol_ids.join(", ")}`);
      }
    } else if (options.impact) {
      console.log(`Impact Report for ${result.changed_file_id}`);
      console.log(`Risk Score: ${result.risk_score.toFixed(2)}`);
      console.log(`Blast Radius: ${result.blast_radius} file(s) affected`);
      console.log(`Direct Dependents: ${result.direct_dependents.join(", ") || "(none)"}`);
      for (const line of result.evidence ?? []) {
        console.log(`  - ${line}`);
      }
    } else {
      console.log(`Architecture: ${result.style}`);
      console.log(`Confidence: ${result.confidence.toFixed(2)}`);
      console.log(`Layers: ${result.layers}`);
      console.log(`Subsystems: ${result.subsystems}`);
      if (result.style === "unknown") {
        for (const line of result.evidence ?? []) {
          console.log(`  - ${line}`);
        }
      }
    }
  });
