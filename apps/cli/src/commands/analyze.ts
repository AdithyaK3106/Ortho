import { Command } from "commander";
import * as path from "path";

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
    const { spawn } = require("child_process");
    const cwd = process.cwd();

    // BUG-003 FIX: Use require.main.filename for robust path resolution
    // This ensures path works regardless of where CLI is run from
    const entryPoint = require.main?.filename || __filename;
    const entryDir = path.dirname(entryPoint);
    const repoRoot = path.resolve(entryDir, "../../..");  // dist -> cli -> apps -> root
    const pythonScript = path.resolve(repoRoot, "apps/cli/src/commands/analyze.py");

    const pythonArgs = ["--repo-root", cwd];
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

    await new Promise<void>((resolve, reject) => {
      const proc = spawn("python", [pythonScript, ...pythonArgs]);

      let output = "";
      proc.stdout.on("data", (data: Buffer) => {
        output += data.toString();
      });

      proc.stderr.on("data", (data: Buffer) => {
        console.error(`Error: ${data.toString()}`);
      });

      proc.on("close", (code: number) => {
        if (code !== 0) {
          reject(new Error(`Command failed with code ${code}`));
          return;
        }

        let result: any;
        try {
          result = JSON.parse(output);
        } catch {
          console.log(output);
          resolve();
          return;
        }

        if (options.format === "json") {
          console.log(JSON.stringify(result));
          resolve();
          return;
        }

        if (options.adrCheck) {
          for (const adr of result.adrs ?? []) {
            console.log(`${adr.adr_id} | ${adr.status} | ${adr.classification}`);
            for (const missing of adr.missing_paths ?? []) {
              console.log(`  missing: ${missing}`);
            }
          }
        } else if (options.reuse) {
          for (const cluster of result.clusters ?? []) {
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
        }

        resolve();
      });
    });
  });
