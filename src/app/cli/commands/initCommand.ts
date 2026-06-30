import type { Command } from "commander";
import {
  createProjectModuleBindings,
  formatInitText,
} from "../../../modules/project/project.index";

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

      console.log(formatInitText(initResult));
    });
}
