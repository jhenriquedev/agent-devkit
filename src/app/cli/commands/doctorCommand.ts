import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import {
  createProjectModuleBindings,
  formatDoctorText,
} from "../../../modules/project/project.index";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterDoctorCommandOptions = {
  appVersion: string;
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

export function registerDoctorCommand(
  program: Command,
  options: RegisterDoctorCommandOptions,
): void {
  const doctorCommand = program
    .command("doctor")
    .description(options.translator.t("cli.doctor.description"))
    .option("--json", options.translator.t("cli.doctor.option.json"));

  doctorCommand.action(
    options.usageLogging.track(
      {
        area: "project",
        command: "doctor",
        options: () => doctorCommand.opts(),
      },
      async (commandOptions: { json?: boolean }) => {
        const bindings = createProjectModuleBindings({
          appVersion: options.appVersion,
        });

        if (bindings.isErr()) {
          throw new Error(bindings.unwrapError());
        }

        const result = await bindings.unwrap().capabilities.doctor.execute();

        if (result.isErr()) {
          throw new Error(result.unwrapError());
        }

        const report = result.unwrap();

        if (commandOptions.json === true) {
          console.log(JSON.stringify(report, null, 2));
          return;
        }

        console.log(
          formatDoctorText(report, {
            color: report.terminal.stdoutIsTTY && !process.env.NO_COLOR,
            translator: options.translator,
          }),
        );
      },
    ),
  );
}
