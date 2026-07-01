import { join } from "node:path";
import {
  BaseCapabilityService,
  type CapabilityExecution,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type ResetResult,
  ResetResultSchema,
  type ResetServiceOptions,
  ResetServiceOptionsSchema,
} from "./reset.entities";
import type { ResetRepositoryPort } from "./reset.repository";

type ResetServiceDependencies = {
  repository: ResetRepositoryPort;
};

export const resetCapabilityConfig = defineCapabilityConfig({
  id: "project.reset",
  moduleId: "project",
  name: "Reset",
  description: "Remove Agent DevKit state from project or global scope after confirmation.",
  kind: "deterministic",
  risk: "destructive",
} as const);

export class ResetService
  extends BaseCapabilityService<typeof resetCapabilityConfig, ResetServiceDependencies>
  implements CapabilityExecution<ResetServiceOptions, ResetResult>
{
  readonly inputSchema = ResetServiceOptionsSchema;
  readonly outputSchema = ResetResultSchema;
  readonly #repository: ResetRepositoryPort;

  constructor(dependencies: ResetServiceDependencies) {
    super(resetCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(options: ResetServiceOptions): Promise<Result<AgentDevKitErrorCode, ResetResult>> {
    const shouldPlan = options.dryRun || options.confirmed !== true;
    const path =
      options.scope === "global"
        ? join(options.homeDirectory, ".agent-devkit")
        : join(options.projectRoot, ".agent-devkit");

    const exists = await this.#repository.exists(path);

    if (exists.isErr()) {
      return Result.fail(exists.unwrapError());
    }

    if (!exists.unwrap()) {
      return Result.ok({
        scope: options.scope,
        status: "missing",
        path,
        removed: false,
      });
    }

    if (shouldPlan) {
      return Result.ok({
        scope: options.scope,
        status: "planned",
        path,
        removed: false,
      });
    }

    const remove = await this.#repository.remove(path);

    if (remove.isErr()) {
      return Result.fail(remove.unwrapError());
    }

    return Result.ok({
      scope: options.scope,
      status: "reset",
      path,
      removed: true,
    });
  }

  invoke(options: ResetServiceOptions): Promise<Result<AgentDevKitErrorCode, ResetResult>> {
    return this.execute(options);
  }
}
