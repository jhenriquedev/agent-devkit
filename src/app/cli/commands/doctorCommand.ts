import type { Command } from "commander";
import {
  createProjectModuleBindings,
  formatDoctorText,
} from "../../../modules/project/project.index";

type RegisterDoctorCommandOptions = {
  appVersion: string;
};

export function registerDoctorCommand(
  program: Command,
  options: RegisterDoctorCommandOptions,
): void {
  program
    .command("doctor")
    .description("inspect the local Agent DevKit environment without changing it")
    .option("--json", "print the doctor report as JSON")
    .action(async (commandOptions: { json?: boolean }) => {
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
        formatDoctorText(report, { color: report.terminal.stdoutIsTTY && !process.env.NO_COLOR }),
      );
    });
}
