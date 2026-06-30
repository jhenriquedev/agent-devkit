import type { Command } from "commander";
import { RunDoctor } from "../../../domain/usecases/RunDoctor";
import { NodePathInspector } from "../../../infra/filesystem/NodePathInspector";
import { NodeSystemInfoProvider } from "../../../infra/process/NodeSystemInfoProvider";
import { formatDoctorText } from "../../viewmodels/doctorViewModel";

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
      const report = await new RunDoctor({
        appVersion: options.appVersion,
        pathInspector: new NodePathInspector(),
        systemInfo: new NodeSystemInfoProvider(),
      }).execute();

      if (commandOptions.json === true) {
        console.log(JSON.stringify(report, null, 2));
        return;
      }

      console.log(
        formatDoctorText(report, { color: report.terminal.stdoutIsTTY && !process.env.NO_COLOR }),
      );
    });
}
