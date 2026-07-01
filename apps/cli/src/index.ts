#!/usr/bin/env node

import { program } from "commander";
import { initCommand } from "./commands/init";
import { indexCommand } from "./commands/index";
import { scanCommand } from "./commands/scan";

program.name("ortho").description("AI Engineering Platform CLI").version("0.1.0");

program.command("init").description("Initialize .ortho/ directory").action(initCommand);

program
  .command("scan")
  .description("Scan and index Python repository")
  .option("--watch", "Enable watch mode (re-index on file changes)")
  .option("--verbose", "Enable verbose output")
  .option("--full", "Full re-index (ignore git state)")
  .action((options) => {
    scanCommand(options).catch((error) => {
      console.error("✗ Scan failed:", error.message);
      process.exit(1);
    });
  });

program
  .command("index")
  .description("Index Python repository (alias for scan)")
  .option("--watch", "Enable watch mode (incremental re-index)")
  .option("--verbose", "Enable verbose output")
  .option("--since <commit>", "Re-index since commit (default: HEAD)")
  .action((options) => {
    indexCommand(options).catch((error) => {
      console.error("✗ Index failed:", error.message);
      process.exit(1);
    });
  });

program.parse(process.argv);
