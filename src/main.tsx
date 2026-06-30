#!/usr/bin/env node
import { Command } from "commander";
import { render } from "ink";
import React from "react";
import packageJson from "../package.json";
import { registerDoctorCommand } from "./app/cli/commands/doctorCommand";
import { registerInitCommand } from "./app/cli/commands/initCommand";
import { registerResetCommand } from "./app/cli/commands/resetCommand";
import { registerUpdateCommand } from "./app/cli/commands/updateCommand";
import { App } from "./app/tui/App";

const program = new Command();

program
  .name("agent")
  .description("Agent DevKit CLI and TUI runtime")
  .version(packageJson.version)
  .argument("[prompt...]", "open the TUI with an optional free-form prompt")
  .action((promptParts: string[]) => {
    const initialPrompt = promptParts.join(" ").trim();
    render(
      React.createElement(App, {
        initialPrompt: initialPrompt.length > 0 ? initialPrompt : undefined,
      }),
    );
  });

registerDoctorCommand(program, { appVersion: packageJson.version });
registerInitCommand(program, { appVersion: packageJson.version });
registerResetCommand(program);
registerUpdateCommand(program);

program.parse(process.argv);
