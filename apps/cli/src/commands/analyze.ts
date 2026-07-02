import { Command } from "commander";

export const analyzeCommand = new Command()
  .name("analyze")
  .description("Full architecture analysis")
  .option("--impact <file>", "Change impact analysis (deferred to task-009)")
  .action(async (options) => {
    const { spawn } = require("child_process");

    return new Promise((resolve, reject) => {
      const impactArg = options.impact ? `--impact=${options.impact}` : "";
      const process = spawn("python", [
        "-m",
        "apps.cli.commands.analyze",
        impactArg,
      ]);

      let output = "";
      process.stdout.on("data", (data: Buffer) => {
        output += data.toString();
      });

      process.stderr.on("data", (data: Buffer) => {
        console.error(`Error: ${data.toString()}`);
      });

      process.on("close", (code: number) => {
        if (code === 0) {
          try {
            const result = JSON.parse(output);
            console.log(`Architecture: ${result.style}`);
            console.log(`Confidence: ${result.confidence.toFixed(2)}`);
            console.log(`Layers: ${result.layers}`);
            console.log(`Subsystems: ${result.subsystems}`);
            resolve(result);
          } catch {
            console.log(output);
            resolve({ status: "ok" });
          }
        } else {
          reject(new Error(`Command failed with code ${code}`));
        }
      });
    });
  });
