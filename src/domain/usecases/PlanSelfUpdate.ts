import type { SelfUpdateResult } from "../entities/SelfUpdateResult";
import type { PackageManager } from "../ports/PackageManager";
import type { PackageRegistry } from "../ports/PackageRegistry";

type PlanSelfUpdateDependencies = {
  currentVersion: string;
  packageName: string;
  packageManager: PackageManager;
  registry: PackageRegistry;
};

type PlanSelfUpdateOptions = {
  dryRun: boolean;
  latest: boolean;
  version?: string;
  yes: boolean;
};

function versionParts(version: string): number[] {
  return version.split(/[.-]/).map((part) => Number.parseInt(part, 10) || 0);
}

function compareVersionsDesc(left: string, right: string): number {
  const leftParts = versionParts(left);
  const rightParts = versionParts(right);
  const length = Math.max(leftParts.length, rightParts.length);

  for (let index = 0; index < length; index += 1) {
    const diff = (rightParts[index] ?? 0) - (leftParts[index] ?? 0);

    if (diff !== 0) {
      return diff;
    }
  }

  return right.localeCompare(left);
}

function compareVersions(left: string, right: string): number {
  const leftParts = versionParts(left);
  const rightParts = versionParts(right);
  const length = Math.max(leftParts.length, rightParts.length);

  for (let index = 0; index < length; index += 1) {
    const diff = (leftParts[index] ?? 0) - (rightParts[index] ?? 0);

    if (diff !== 0) {
      return diff;
    }
  }

  return left.localeCompare(right);
}

export class PlanSelfUpdate {
  readonly #currentVersion: string;
  readonly #packageName: string;
  readonly #packageManager: PackageManager;
  readonly #registry: PackageRegistry;

  constructor(dependencies: PlanSelfUpdateDependencies) {
    this.#currentVersion = dependencies.currentVersion;
    this.#packageName = dependencies.packageName;
    this.#packageManager = dependencies.packageManager;
    this.#registry = dependencies.registry;
  }

  async execute(options: PlanSelfUpdateOptions): Promise<SelfUpdateResult> {
    const packageVersions = await this.#registry.getPackageVersions(this.#packageName);
    const latestVersion =
      packageVersions.distTags.latest ?? packageVersions.versions.at(-1) ?? this.#currentVersion;
    const explicitVersion = options.version !== undefined;
    const selectedVersion = options.version ?? (options.latest ? latestVersion : latestVersion);
    const listedVersions = Array.from(
      new Set([...packageVersions.versions, this.#currentVersion, selectedVersion]),
    );

    if (!explicitVersion && compareVersions(latestVersion, this.#currentVersion) <= 0) {
      return {
        status: "current",
        packageName: this.#packageName,
        currentVersion: this.#currentVersion,
        selectedVersion: this.#currentVersion,
        command: "",
        executed: false,
        versions: listedVersions.sort(compareVersionsDesc).map((version) => ({
          version,
          current: version === this.#currentVersion,
          latest: version === latestVersion,
          selected: version === this.#currentVersion,
        })),
      };
    }

    const dryRun = options.dryRun || !options.yes;
    const install = await this.#packageManager.installGlobal(this.#packageName, selectedVersion, {
      dryRun,
    });
    const versions = listedVersions.sort(compareVersionsDesc).map((version) => ({
      version,
      current: version === this.#currentVersion,
      latest: version === latestVersion,
      selected: version === selectedVersion,
    }));

    return {
      status: install.executed ? "updated" : "planned",
      packageName: this.#packageName,
      currentVersion: this.#currentVersion,
      selectedVersion,
      command: install.command,
      executed: install.executed,
      versions,
    };
  }
}
