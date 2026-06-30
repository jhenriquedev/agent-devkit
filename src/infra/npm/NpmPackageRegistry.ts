import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { PackageRegistry, PackageVersions } from "../../domain/ports/PackageRegistry";

const execFileAsync = promisify(execFile);

export class NpmPackageRegistry implements PackageRegistry {
  async getPackageVersions(packageName: string): Promise<PackageVersions> {
    const testPayload = process.env.AGENT_DEVKIT_TEST_NPM_VIEW;

    if (testPayload) {
      return JSON.parse(testPayload) as PackageVersions;
    }

    const [{ stdout: versionsOutput }, { stdout: distTagsOutput }] = await Promise.all([
      execFileAsync("npm", ["view", packageName, "versions", "--json"]),
      execFileAsync("npm", ["view", packageName, "dist-tags", "--json"]),
    ]);

    return {
      versions: JSON.parse(versionsOutput) as string[],
      distTags: JSON.parse(distTagsOutput) as Record<string, string | undefined>,
    };
  }
}
