import { homedir } from "node:os";
import type { Command } from "commander";
import {
  createProjectModuleBindings,
  formatResetText,
} from "../../../modules/project/project.index";

type RegisterResetCommandOptions = {
  appVersion: string;
};

export function registerResetCommand(program: Command, options: RegisterResetCommandOptions): void {
  program
    .command("reset")
    .description("remove Agent DevKit state from the current project or global scope")
    .option("-g, --global", "reset global state under ~/.agent-devkit")
    .option("--dry-run", "show what would be removed without deleting files")
    .option("--json", "print the reset result as JSON")
    .option("--yes", "confirm state removal")
    .action(
      async (commandOptions: {
        dryRun?: boolean;
        global?: boolean;
        json?: boolean;
        yes?: boolean;
      }) => {
        const dryRun = commandOptions.dryRun === true || commandOptions.yes !== true;
        const bindings = createProjectModuleBindings({
          appVersion: options.appVersion,
        });

        if (bindings.isErr()) {
          throw new Error(bindings.unwrapError());
        }

        const result = await bindings.unwrap().capabilities.reset.execute({
          dryRun,
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

        console.log(formatResetText(resetResult));
      },
    );
}
