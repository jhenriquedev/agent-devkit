import {
  BaseCapabilityService,
  type CapabilityApproval,
  type CapabilityEffect,
  type CapabilityInvocationContext,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type ModelsRegistryOptions,
  ModelsRegistryOptionsSchema,
  type ModelsRegistryResult,
  ModelsRegistryResultSchema,
} from "./registry.entities";
import type { ModelsRegistryRepositoryPort } from "./registry.repository";

type ModelsRegistryServiceDependencies = {
  repository: ModelsRegistryRepositoryPort;
};

export const modelsRegistryCapabilityConfig = defineCapabilityConfig({
  id: "models.registry",
  moduleId: "models",
  name: "Models registry",
  description: "List, install, update, remove and select local LLM model artifacts.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

export class ModelsRegistryService extends BaseCapabilityService<
  typeof modelsRegistryCapabilityConfig,
  ModelsRegistryServiceDependencies
> {
  readonly inputSchema = ModelsRegistryOptionsSchema;
  readonly outputSchema = ModelsRegistryResultSchema;
  readonly #repository: ModelsRegistryRepositoryPort;

  constructor(dependencies: ModelsRegistryServiceDependencies) {
    super(modelsRegistryCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: ModelsRegistryOptions,
  ): Promise<Result<AgentDevKitErrorCode, ModelsRegistryResult>> {
    const parsed = this.inputSchema.safeParse(options);

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    return this.#run(parsed.data);
  }

  invoke(
    options: ModelsRegistryOptions,
    _context: CapabilityInvocationContext,
  ): Promise<Result<AgentDevKitErrorCode, ModelsRegistryResult>> {
    return this.execute(options);
  }

  override approvalForInput(input: ModelsRegistryOptions): CapabilityApproval {
    if (input.action === "list" || input.action === "status") {
      return { reason: "Models registry read action.", required: false };
    }

    return {
      reason: "Models registry action writes local model state.",
      required: true,
    };
  }

  override effectsForInput(input: ModelsRegistryOptions): CapabilityEffect[] {
    if (input.action === "list" || input.action === "status") {
      return [{ operation: "read", scope: "none" }];
    }

    if (input.action === "uninstall") {
      return [{ operation: "delete", scope: "global" }];
    }

    return [{ operation: "write", scope: "global" }];
  }

  async #run(
    options: ModelsRegistryOptions,
  ): Promise<Result<AgentDevKitErrorCode, ModelsRegistryResult>> {
    const directory = this.#repository.directory();

    if (options.action === "list") {
      const models = await this.#repository.listModels();

      if (models.isErr()) {
        return Result.fail(models.unwrapError());
      }

      const defaultId = await this.#repository.defaultId();

      return Result.ok({
        action: "list",
        directory,
        models: models.unwrap(),
        defaultId: defaultId.isOk() ? defaultId.unwrap() : undefined,
      });
    }

    if (options.action === "status") {
      const models = await this.#repository.statusModels(options.id);

      return models.isOk()
        ? Result.ok({ action: "status", directory, models: models.unwrap() })
        : Result.fail(models.unwrapError());
    }

    if (options.action === "install") {
      const model = await this.#repository.install(options.id);

      return model.isOk()
        ? Result.ok({ action: "install", directory, model: model.unwrap() })
        : Result.fail(model.unwrapError());
    }

    if (options.action === "uninstall") {
      const removed = await this.#repository.uninstall(options.id);

      return removed.isOk()
        ? Result.ok({
            action: "uninstall",
            directory,
            id: removed.unwrap().id,
            removed: removed.unwrap().removed,
          })
        : Result.fail(removed.unwrapError());
    }

    if (options.action === "update") {
      const models = await this.#repository.update(options.id);

      return models.isOk()
        ? Result.ok({ action: "update", directory, models: models.unwrap() })
        : Result.fail(models.unwrapError());
    }

    const defaultId = await this.#repository.setDefault(options.id, options.role);

    return defaultId.isOk()
      ? Result.ok({ action: "use", directory, defaultId: defaultId.unwrap(), role: options.role })
      : Result.fail(defaultId.unwrapError());
  }
}
