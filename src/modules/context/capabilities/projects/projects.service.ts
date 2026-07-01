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
  type ContextProjectsOptions,
  ContextProjectsOptionsSchema,
  type ContextProjectsResult,
  ContextProjectsResultSchema,
} from "./projects.entities";
import type { ContextProjectsRepositoryPort } from "./projects.repository";

type ContextProjectsServiceDependencies = {
  repository: ContextProjectsRepositoryPort;
};

export const contextProjectsCapabilityConfig = defineCapabilityConfig({
  id: "context.projects",
  moduleId: "context",
  name: "Context Projects",
  description: "Create, list and manage Agent DevKit context projects.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

export class ContextProjectsService extends BaseCapabilityService<
  typeof contextProjectsCapabilityConfig,
  ContextProjectsServiceDependencies,
  ContextProjectsOptions,
  ContextProjectsResult
> {
  readonly inputSchema = ContextProjectsOptionsSchema;
  readonly outputSchema = ContextProjectsResultSchema;
  readonly #repository: ContextProjectsRepositoryPort;

  constructor(dependencies: ContextProjectsServiceDependencies) {
    super(contextProjectsCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: ContextProjectsOptions,
  ): Promise<Result<AgentDevKitErrorCode, ContextProjectsResult>> {
    const parsed = this.inputSchema.safeParse(options);

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const input = parsed.data;

    if (input.action === "list") {
      return (await this.#repository.list(input)).map((projects) => ({
        action: "list",
        projects,
      }));
    }

    if (input.action === "create") {
      return (await this.#repository.create(input)).map((project) => ({
        action: "create",
        project,
      }));
    }

    if (input.action === "show") {
      return (await this.#repository.show(input.projectId)).map((project) => ({
        action: "show",
        project,
      }));
    }

    if (input.action === "update") {
      return (await this.#repository.update(input)).map((project) => ({
        action: "update",
        project,
      }));
    }

    if (input.action === "archive") {
      return (await this.#repository.archive(input.projectId)).map((project) => ({
        action: "archive",
        project,
      }));
    }

    return (await this.#repository.delete(input.projectId, input.hard)).map((removed) => ({
      action: "delete",
      hard: input.hard === true,
      projectId: input.projectId,
      removed,
    }));
  }

  invoke(
    input: ContextProjectsOptions,
    _context: CapabilityInvocationContext,
  ): Promise<Result<AgentDevKitErrorCode, ContextProjectsResult>> {
    return this.execute(input);
  }

  override approvalForInput(input: ContextProjectsOptions): CapabilityApproval {
    if (input.action === "list" || input.action === "show") {
      return { reason: "Context project read action.", required: false };
    }

    if (input.action === "delete" && input.hard === true) {
      return {
        reason: "Context project hard delete removes durable state.",
        required: true,
      };
    }

    return {
      reason: "Context project action writes global state.",
      required: true,
    };
  }

  override effectsForInput(input: ContextProjectsOptions): CapabilityEffect[] {
    if (input.action === "list" || input.action === "show") {
      return [{ operation: "read", scope: "none" }];
    }

    if (input.action === "delete" && input.hard === true) {
      return [{ operation: "delete", scope: "global" }];
    }

    return [{ operation: "write", scope: "global" }];
  }
}
