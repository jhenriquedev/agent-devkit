import { join } from "node:path";
import type { ResetResult, ResetScope } from "../entities/ResetResult";
import type { StateResetRepository } from "../ports/StateResetRepository";

type ResetStateDependencies = {
  homeDirectory: string;
  projectRoot: string;
  repository: StateResetRepository;
};

type ResetStateOptions = {
  dryRun: boolean;
  scope: ResetScope;
};

export class ResetState {
  readonly #homeDirectory: string;
  readonly #projectRoot: string;
  readonly #repository: StateResetRepository;

  constructor(dependencies: ResetStateDependencies) {
    this.#homeDirectory = dependencies.homeDirectory;
    this.#projectRoot = dependencies.projectRoot;
    this.#repository = dependencies.repository;
  }

  async execute(options: ResetStateOptions): Promise<ResetResult> {
    const path =
      options.scope === "global"
        ? join(this.#homeDirectory, ".agent-devkit")
        : join(this.#projectRoot, ".agent-devkit");

    const exists = await this.#repository.exists(path);

    if (!exists) {
      return {
        scope: options.scope,
        status: "missing",
        path,
        removed: false,
      };
    }

    if (options.dryRun) {
      return {
        scope: options.scope,
        status: "planned",
        path,
        removed: false,
      };
    }

    await this.#repository.remove(path);

    return {
      scope: options.scope,
      status: "reset",
      path,
      removed: true,
    };
  }
}
