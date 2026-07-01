import { homedir } from "node:os";
import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import {
  createProjectModuleBindings,
  formatResetText,
} from "../../../modules/project/project.index";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterResetCommandOptions = {
  appVersion: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

export function registerResetCommand(program: Command, options: RegisterResetCommandOptions): void {
  const resetCommand = program
    .command("reset")
    .description(options.translator.t("cli.reset.description"))
    .option("-g, --global", options.translator.t("cli.reset.option.global"))
    .option("--dry-run", options.translator.t("cli.reset.option.dryRun"))
    .option("--json", options.translator.t("cli.reset.option.json"))
    .option("--yes", options.translator.t("cli.reset.option.yes"));

  resetCommand.action(
    options.usageLogging.track(
      {
        area: "project",
        command: "reset",
        options: () => resetCommand.opts(),
      },
      async (commandOptions: {
        dryRun?: boolean;
        global?: boolean;
        json?: boolean;
        yes?: boolean;
      }) => {
        const bindings = createProjectModuleBindings({
          appVersion: options.appVersion,
        });

        if (bindings.isErr()) {
          throw new Error(bindings.unwrapError());
        }

        const result = await bindings.unwrap().capabilities.reset.execute({
          confirmed: commandOptions.yes === true,
          dryRun: commandOptions.dryRun === true,
          homeDirectory: homedir(),
          projectRoot: process.cwd(),
          scope: commandOptions.global === true ? "global" : "project",
        });

        if (result.isErr()) {
          throw new Error(result.unwrapError());
        }

        const resetResult = result.unwrap();

        if (commandOptions.json === true) {
          console.log(JSON.stringify(resetResult, null, 2));
          return;
        }

        console.log(formatResetText(resetResult, options.translator));
      },
    ),
  );
}
