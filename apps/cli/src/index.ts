#!/usr/bin/env node

import { program } from "commander";
import { initCommand } from "./commands/init";

program.name("ortho").description("AI Engineering Platform CLI").version("0.1.0");

program.command("init").description("Initialize .ortho/ directory").action(initCommand);

program.parse(process.argv);
