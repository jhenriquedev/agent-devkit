import type { Command } from "commander";
import packageJson from "../../../../package.json";
import { createSelfModuleBindings, formatUpdateText } from "../../../modules/self/self.index";

export function registerUpdateCommand(program: Command): void {
  program
    .command("update")
    .argument("[version]", "specific package version to install")
    .description("list npm versions and plan or run a self-update")
    .option("--dry-run", "show the planned npm update without installing")
    .option("--json", "print the update plan as JSON")
    .option("--latest", "select the npm latest version")
    .option("--yes", "confirm installation of the selected version")
    .action(
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

        console.log(formatUpdateText(updateResult));
      },
    );
}
