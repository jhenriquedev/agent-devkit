import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type { PackageInstallResult, PackageVersions } from "./update.entities";

const execFileAsync = promisify(execFile);

export interface UpdateRepositoryPort extends CapabilityRepositoryPort {
  getPackageVersions(packageName: string): Promise<Result<AgentDevKitErrorCode, PackageVersions>>;
  installGlobal(
    packageName: string,
    version: string,
    options: { dryRun: boolean },
  ): Promise<Result<AgentDevKitErrorCode, PackageInstallResult>>;
}

export class UpdateRepository implements UpdateRepositoryPort {
  readonly repositoryId = "self.update.repository";

  async getPackageVersions(
    packageName: string,
  ): Promise<Result<AgentDevKitErrorCode, PackageVersions>> {
    try {
      const [{ stdout: versionsOutput }, { stdout: distTagsOutput }] = await Promise.all([
        execFileAsync("npm", ["view", packageName, "versions", "--json"]),
        execFileAsync("npm", ["view", packageName, "dist-tags", "--json"]),
      ]);

      return Result.ok({
        versions: JSON.parse(versionsOutput) as string[],
        distTags: JSON.parse(distTagsOutput) as Record<string, string | undefined>,
      });
    } catch {
      return Result.fail(ErrorCodes.PackageRegistryFailed);
    }
  }

  async installGlobal(
    packageName: string,
    version: string,
    options: { dryRun: boolean },
  ): Promise<Result<AgentDevKitErrorCode, PackageInstallResult>> {
    const command = `npm install -g ${packageName}@${version}`;

    try {
      if (!options.dryRun) {
        await execFileAsync("npm", ["install", "-g", `${packageName}@${version}`]);
      }

      return Result.ok({
        command,
        executed: !options.dryRun,
      });
    } catch {
      return Result.fail(ErrorCodes.PackageInstallFailed);
    }
  }
}
