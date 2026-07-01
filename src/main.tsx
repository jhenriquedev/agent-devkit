#!/usr/bin/env node
import { Command } from "commander";
import { render } from "ink";
import React from "react";
import packageJson from "../package.json";
import { registerDoctorCommand } from "./app/cli/commands/doctorCommand";
import { registerInitCommand } from "./app/cli/commands/initCommand";
import { registerInstallCommand } from "./app/cli/commands/installCommand";
import { registerLogsCommand } from "./app/cli/commands/logsCommand";
import { registerMcpCommand } from "./app/cli/commands/mcpCommand";
import { registerPreferencesCommand } from "./app/cli/commands/preferencesCommand";
import { registerResetCommand } from "./app/cli/commands/resetCommand";
import { registerRunCommand } from "./app/cli/commands/runCommand";
import { registerSecretsCommand } from "./app/cli/commands/secretsCommand";
import { registerToolsCommand } from "./app/cli/commands/toolsCommand";
import { registerUpdateCommand } from "./app/cli/commands/updateCommand";
import {
  configureLocalizedHelp,
  createCliTranslator,
  loadCliUserPreferences,
} from "./app/cli/i18n";
import { CliUsageLoggingMiddleware } from "./app/cli/usageLogging";
import { App } from "./app/tui/App";
import { JsonTechnicalLogger } from "./infra/logging/json_technical_logger";
import { JsonUsageLogger } from "./infra/logging/json_usage_logger";

const program = new Command();
const userPreferences = loadCliUserPreferences();
const translator = createCliTranslator();
const usageLogging = new CliUsageLoggingMiddleware({
  logger: new JsonUsageLogger({ retentionDays: userPreferences.logRetentionDays }),
  technicalLogger: new JsonTechnicalLogger({ retentionDays: userPreferences.logRetentionDays }),
});
configureLocalizedHelp(program, translator);

program
  .name("agent")
  .description(translator.t("cli.root.description"))
  .version(packageJson.version, "-v, --version", translator.t("cli.version.option"))
  .argument("[prompt...]", translator.t("cli.root.promptArgument"))
  .action(
    usageLogging.track({ area: "user", command: "tui" }, (promptParts: string[]) => {
      const initialPrompt = promptParts.join(" ").trim();
      render(
        React.createElement(App, {
          initialPrompt: initialPrompt.length > 0 ? initialPrompt : undefined,
          translator,
        }),
      );
    }),
  );

registerDoctorCommand(program, { appVersion: packageJson.version, translator, usageLogging });
registerInitCommand(program, { appVersion: packageJson.version, translator, usageLogging });
registerInstallCommand(program, {
  currentVersion: packageJson.version,
  packageName: packageJson.name,
  translator,
  usageLogging,
});
registerLogsCommand(program, { translator, usageLogging });
registerMcpCommand(program, {
  currentVersion: packageJson.version,
  packageName: packageJson.name,
  translator,
  usageLogging,
});
registerPreferencesCommand(program, { translator, usageLogging });
registerResetCommand(program, { appVersion: packageJson.version, translator, usageLogging });
registerRunCommand(program, {
  currentVersion: packageJson.version,
  packageName: packageJson.name,
  translator,
  usageLogging,
});
registerSecretsCommand(program, { translator, usageLogging });
registerToolsCommand(program, {
  currentVersion: packageJson.version,
  packageName: packageJson.name,
  translator,
  usageLogging,
});
registerUpdateCommand(program, { translator, usageLogging });

await program.parseAsync(process.argv);
