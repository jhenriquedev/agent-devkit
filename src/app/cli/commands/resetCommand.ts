import { homedir } from "node:os";
import type { Command } from "commander";
import { ResetState } from "../../../domain/usecases/ResetState";
import { FileStateResetRepository } from "../../../infra/repositories/FileStateResetRepository";
import { formatResetText } from "../../viewmodels/resetViewModel";

export function registerResetCommand(program: Command): void {
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
        const result = await new ResetState({
          homeDirectory: homedir(),
          projectRoot: process.cwd(),
          repository: new FileStateResetRepository(),
        }).execute({
          dryRun,
          scope: commandOptions.global === true ? "global" : "project",
        });

        if (commandOptions.json === true) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log(formatResetText(result));
      },
    );
}
