import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import {
  createProjectModuleBindings,
  formatInitText,
} from "../../../modules/project/project.index";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterInitCommandOptions = {
  appVersion: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

export function registerInitCommand(program: Command, options: RegisterInitCommandOptions): void {
  const initCommand = program
    .command("init")
    .description(options.translator.t("cli.init.description"))
    .option("--dry-run", options.translator.t("cli.init.option.dryRun"))
    .option("--json", options.translator.t("cli.init.option.json"));

  initCommand.action(
    options.usageLogging.track(
      {
        area: "project",
        command: "init",
        options: () => initCommand.opts(),
      },
      async (commandOptions: { dryRun?: boolean; json?: boolean }) => {
        const bindings = createProjectModuleBindings({
          appVersion: options.appVersion,
        });

        if (bindings.isErr()) {
          throw new Error(bindings.unwrapError());
        }

        const result = await bindings.unwrap().capabilities.init.execute({
          dryRun: commandOptions.dryRun === true,
          projectRoot: process.cwd(),
        });

        if (result.isErr()) {
          throw new Error(result.unwrapError());
        }

        const initResult = result.unwrap();

        if (commandOptions.json === true) {
          console.log(JSON.stringify(initResult, null, 2));
          return;
        }

        console.log(formatInitText(initResult, options.translator));
      },
    ),
  );
}
