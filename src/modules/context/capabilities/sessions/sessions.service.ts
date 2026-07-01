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
  type ContextSessionsOptions,
  ContextSessionsOptionsSchema,
  type ContextSessionsResult,
  ContextSessionsResultSchema,
} from "./sessions.entities";
import type { ContextSessionsRepositoryPort } from "./sessions.repository";

type ContextSessionsServiceDependencies = {
  repository: ContextSessionsRepositoryPort;
};

export const contextSessionsCapabilityConfig = defineCapabilityConfig({
  id: "context.sessions",
  moduleId: "context",
  name: "Context Sessions",
  description: "Create, search, resume and manage Agent DevKit context sessions.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

export class ContextSessionsService extends BaseCapabilityService<
  typeof contextSessionsCapabilityConfig,
  ContextSessionsServiceDependencies,
  ContextSessionsOptions,
  ContextSessionsResult
> {
  readonly inputSchema = ContextSessionsOptionsSchema;
  readonly outputSchema = ContextSessionsResultSchema;
  readonly #repository: ContextSessionsRepositoryPort;

  constructor(dependencies: ContextSessionsServiceDependencies) {
    super(contextSessionsCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: ContextSessionsOptions,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionsResult>> {
    const parsed = this.inputSchema.safeParse(options);

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const input = parsed.data;

    if (input.action === "list") {
      return (await this.#repository.list(input)).map((sessions) => ({
        action: "list",
        sessions,
      }));
    }

    if (input.action === "create") {
      return (await this.#repository.create(input)).map((session) => ({
        action: "create",
        session,
      }));
    }

    if (input.action === "append-message") {
      return (await this.#repository.appendMessage(input)).map((result) => ({
        action: "append-message",
        ...result,
      }));
    }

    if (input.action === "show") {
      return (await this.#repository.show(input)).map((result) => ({
        action: "show",
        ...result,
      }));
    }

    if (input.action === "search") {
      return (await this.#repository.search(input)).map((results) => ({
        action: "search",
        query: input.query,
        results,
      }));
    }

    if (input.action === "resume") {
      return (await this.#repository.resume(input.sessionId)).map((result) => ({
        action: "resume",
        index: result.index,
        messages: result.messages ?? [],
        session: result.session,
      }));
    }

    if (input.action === "archive") {
      return (await this.#repository.archive(input.sessionId)).map((result) => ({
        action: "archive",
        index: result.index,
        session: result.session,
      }));
    }

    return (await this.#repository.delete(input.sessionId, input.hard)).map((removed) => ({
      action: "delete",
      hard: input.hard === true,
      removed,
      sessionId: input.sessionId,
    }));
  }

  invoke(
    input: ContextSessionsOptions,
    _context: CapabilityInvocationContext,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionsResult>> {
    return this.execute(input);
  }

  override approvalForInput(input: ContextSessionsOptions): CapabilityApproval {
    if (input.action === "delete" && input.hard === true) {
      return {
        reason: "Context session hard delete removes durable memory.",
        required: true,
      };
    }

    return { reason: "Context session action is safe for local memory.", required: false };
  }

  override effectsForInput(input: ContextSessionsOptions): CapabilityEffect[] {
    if (input.action === "list" || input.action === "show" || input.action === "search") {
      return [{ operation: "read", scope: "none" }];
    }

    if (input.action === "delete" && input.hard === true) {
      return [{ operation: "delete", scope: "global" }];
    }

    return [{ operation: "write", scope: "global" }];
  }
}
