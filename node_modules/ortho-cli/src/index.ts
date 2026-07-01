#!/usr/bin/env node

import { program } from "commander";
import { initCommand } from "./commands/init";
import { indexCommand } from "./commands/index";

program.name("ortho").description("AI Engineering Platform CLI").version("0.1.0");

program.command("init").description("Initialize .ortho/ directory").action(initCommand);

program
  .command("index")
  .description("Index Python repository")
  .option("--watch", "Enable watch mode (incremental re-index)")
  .option("--verbose", "Enable verbose output")
  .action((options) => {
    indexCommand(options).catch((error) => {
      console.error("✗ Index failed:", error.message);
      process.exit(1);
    });
  });

program.parse(process.argv);
