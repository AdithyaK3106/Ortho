#!/usr/bin/env node

import { program } from "commander";
import { initCommand } from "./commands/init";
import { indexCommand } from "./commands/index";
import { scanCommand } from "./commands/scan";
import { analyzeCommand } from "./commands/analyze";
// BUG-005 FIX: Import task-013 workflow commands
import { runCommand } from "./commands/run";
import { statusCommand } from "./commands/status";
import { approveCommand } from "./commands/approve";
import { rejectCommand } from "./commands/reject";
import { historyCommand } from "./commands/history";
import { contextCommand } from "./commands/context";
import {
  guardrailsCommand,
  decideCommand,
  planCommand,
  refactorCommand,
  memoryCommand,
} from "./commands/copilot";

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

program.addCommand(analyzeCommand);

// BUG-005 FIX: Register task-013 workflow commands
program.addCommand(runCommand);
program.addCommand(statusCommand);
program.addCommand(approveCommand);
program.addCommand(rejectCommand);
program.addCommand(historyCommand);
program.addCommand(contextCommand);

// task-021: engineering copilot commands (real CliCommands engines)
program.addCommand(guardrailsCommand);
program.addCommand(decideCommand);
program.addCommand(planCommand);
program.addCommand(refactorCommand);

// task-024: memory search (query workflow_run artifacts)
program.addCommand(memoryCommand);

program.parse(process.argv);
