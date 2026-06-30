import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { PackageInstallResult, PackageManager } from "../../domain/ports/PackageManager";

const execFileAsync = promisify(execFile);

export class NpmPackageManager implements PackageManager {
  async installGlobal(
    packageName: string,
    version: string,
    options: { dryRun: boolean },
  ): Promise<PackageInstallResult> {
    const command = `npm install -g ${packageName}@${version}`;

    if (!options.dryRun) {
      await execFileAsync("npm", ["install", "-g", `${packageName}@${version}`]);
    }

    return {
      command,
      executed: !options.dryRun,
    };
  }
}
