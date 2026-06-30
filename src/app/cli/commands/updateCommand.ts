import type { Command } from "commander";
import packageJson from "../../../../package.json";
import { PlanSelfUpdate } from "../../../domain/usecases/PlanSelfUpdate";
import { NpmPackageManager } from "../../../infra/npm/NpmPackageManager";
import { NpmPackageRegistry } from "../../../infra/npm/NpmPackageRegistry";
import { formatUpdateText } from "../../viewmodels/updateViewModel";

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
        const result = await new PlanSelfUpdate({
          currentVersion: packageJson.version,
          packageName: packageJson.name,
          packageManager: new NpmPackageManager(),
          registry: new NpmPackageRegistry(),
        }).execute({
          dryRun: commandOptions.dryRun === true,
          latest: commandOptions.latest === true,
          version: targetVersion,
          yes: commandOptions.yes === true,
        });

        if (commandOptions.json === true) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        console.log(formatUpdateText(result));
      },
    );
}
