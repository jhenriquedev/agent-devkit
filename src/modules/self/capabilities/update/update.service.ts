import {
  BaseCapabilityService,
  type CapabilityExecution,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type { SelfUpdateResult } from "./update.entities";
import type { UpdateRepositoryPort } from "./update.repository";

type UpdateServiceDependencies = {
  currentVersion: string;
  packageName: string;
  repository: UpdateRepositoryPort;
};

type UpdateServiceOptions = {
  dryRun: boolean;
  latest: boolean;
  version?: string;
  yes: boolean;
};

function versionParts(version: string): number[] {
  return version.split(/[.-]/).map((part) => Number.parseInt(part, 10) || 0);
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

function compareVersionsDesc(left: string, right: string): number {
  return compareVersions(right, left);
}

export const updateCapabilityConfig = defineCapabilityConfig({
  id: "self.update",
  moduleId: "self",
  name: "Update",
  description: "Plan or execute Agent DevKit package updates through npm.",
  kind: "external",
  risk: "external-write",
} as const);

export class UpdateService
  extends BaseCapabilityService<typeof updateCapabilityConfig, UpdateServiceDependencies>
  implements CapabilityExecution<UpdateServiceOptions, SelfUpdateResult>
{
  readonly #currentVersion: string;
  readonly #packageName: string;
  readonly #repository: UpdateRepositoryPort;

  constructor(dependencies: UpdateServiceDependencies) {
    super(updateCapabilityConfig, dependencies);
    this.#currentVersion = dependencies.currentVersion;
    this.#packageName = dependencies.packageName;
    this.#repository = dependencies.repository;
  }

  async execute(
    options: UpdateServiceOptions,
  ): Promise<Result<AgentDevKitErrorCode, SelfUpdateResult>> {
    const packageVersions = await this.#repository.getPackageVersions(this.#packageName);

    if (packageVersions.isErr()) {
      return Result.fail(packageVersions.unwrapError());
    }

    const versionsPayload = packageVersions.unwrap();
    const latestVersion =
      versionsPayload.distTags.latest ?? versionsPayload.versions.at(-1) ?? this.#currentVersion;
    const explicitVersion = options.version !== undefined;
    const selectedVersion = options.version ?? (options.latest ? latestVersion : latestVersion);
    const listedVersions = Array.from(
      new Set([...versionsPayload.versions, this.#currentVersion, selectedVersion]),
    );

    if (!explicitVersion && compareVersions(latestVersion, this.#currentVersion) <= 0) {
      return Result.ok({
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
      });
    }

    const dryRun = options.dryRun || !options.yes;
    const install = await this.#repository.installGlobal(this.#packageName, selectedVersion, {
      dryRun,
    });

    if (install.isErr()) {
      return Result.fail(install.unwrapError());
    }

    return Result.ok({
      status: install.unwrap().executed ? "updated" : "planned",
      packageName: this.#packageName,
      currentVersion: this.#currentVersion,
      selectedVersion,
      command: install.unwrap().command,
      executed: install.unwrap().executed,
      versions: listedVersions.sort(compareVersionsDesc).map((version) => ({
        version,
        current: version === this.#currentVersion,
        latest: version === latestVersion,
        selected: version === selectedVersion,
      })),
    });
  }
}
