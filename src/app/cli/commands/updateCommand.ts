import type { Command } from "commander";
import packageJson from "../../../../package.json";
import type { Translator } from "../../../infra/bases/i18n";
import { createSelfModuleBindings, formatUpdateText } from "../../../modules/self/self.index";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterUpdateCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

export function registerUpdateCommand(
  program: Command,
  options: RegisterUpdateCommandOptions,
): void {
  const updateCommand = program
    .command("update")
    .argument("[version]", options.translator.t("cli.update.argument.version"))
    .description(options.translator.t("cli.update.description"))
    .option("--dry-run", options.translator.t("cli.update.option.dryRun"))
    .option("--json", options.translator.t("cli.update.option.json"))
    .option("--latest", options.translator.t("cli.update.option.latest"))
    .option("--yes", options.translator.t("cli.update.option.yes"));

  updateCommand.action(
    options.usageLogging.track(
      {
        area: "self",
        command: "update",
        options: () => updateCommand.opts(),
      },
      async (
        targetVersion: string | undefined,
        commandOptions: {
          dryRun?: boolean;
          json?: boolean;
          latest?: boolean;
          yes?: boolean;
        },
      ) => {
        const bindings = createSelfModuleBindings({
          currentVersion: packageJson.version,
          packageName: packageJson.name,
        });

        if (bindings.isErr()) {
          throw new Error(bindings.unwrapError());
        }

        const result = await bindings.unwrap().capabilities.update.execute({
          dryRun: commandOptions.dryRun === true,
          latest: commandOptions.latest === true,
          version: targetVersion,
          yes: commandOptions.yes === true,
        });

        if (result.isErr()) {
          throw new Error(result.unwrapError());
        }

        const updateResult = result.unwrap();

        if (commandOptions.json === true) {
          console.log(JSON.stringify(updateResult, null, 2));
          return;
        }

        console.log(formatUpdateText(updateResult, options.translator));
      },
    ),
  );
}
