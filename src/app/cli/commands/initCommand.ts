import type { Command } from "commander";
import { InitializeProject } from "../../../domain/usecases/InitializeProject";
import { FileProjectStateRepository } from "../../../infra/repositories/FileProjectStateRepository";
import { formatInitText } from "../../viewmodels/initViewModel";

type RegisterInitCommandOptions = {
  appVersion: string;
};

export function registerInitCommand(program: Command, options: RegisterInitCommandOptions): void {
  program
    .command("init")
    .description("initialize Agent DevKit project state in the current directory")
    .option("--dry-run", "show what would be created without writing files")
    .option("--json", "print the initialization result as JSON")
    .action(async (commandOptions: { dryRun?: boolean; json?: boolean }) => {
      const result = await new InitializeProject({
        appVersion: options.appVersion,
        projectRoot: process.cwd(),
        repository: new FileProjectStateRepository(),
      }).execute({ dryRun: commandOptions.dryRun === true });

      if (commandOptions.json === true) {
        console.log(JSON.stringify(result, null, 2));
        return;
      }

      console.log(formatInitText(result));
    });
}
