import {
  BaseCapabilityService,
  type CapabilityApproval,
  type CapabilityEffect,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type CliAliasOptions,
  CliAliasOptionsSchema,
  type CliAliasResult,
  CliAliasResultSchema,
} from "./cliAlias.entities";
import type { CliAliasRepositoryPort } from "./cliAlias.repository";

type CliAliasServiceDependencies = {
  repository: CliAliasRepositoryPort;
};

export const cliAliasCapabilityConfig = defineCapabilityConfig({
  id: "user.cliAlias",
  moduleId: "user",
  name: "CLI alias",
  description: "Create and manage a local command alias for the Agent DevKit CLI.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

export class CliAliasService extends BaseCapabilityService<
  typeof cliAliasCapabilityConfig,
  CliAliasServiceDependencies,
  CliAliasOptions,
  CliAliasResult
> {
  readonly inputSchema = CliAliasOptionsSchema;
  readonly outputSchema = CliAliasResultSchema;
  readonly #repository: CliAliasRepositoryPort;

  constructor(dependencies: CliAliasServiceDependencies) {
    super(cliAliasCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(options: CliAliasOptions): Promise<Result<AgentDevKitErrorCode, CliAliasResult>> {
    const parsed = this.inputSchema.safeParse(options);

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const input = parsed.data;
    const result =
      input.action === "set"
        ? await this.#set(input.name, input.force)
        : input.action === "remove"
          ? await this.#remove()
          : input.action === "sync"
            ? await this.#sync()
            : await this.#view(input.action === "shell" ? "shell" : "view");

    if (result.isErr()) {
      return Result.fail(result.unwrapError());
    }

    const output = this.outputSchema.safeParse(result.unwrap());
    return output.success ? Result.ok(output.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  invoke(options: CliAliasOptions): Promise<Result<AgentDevKitErrorCode, CliAliasResult>> {
    return this.execute(options);
  }

  override approvalForInput(input: CliAliasOptions): CapabilityApproval {
    if (input.action === "status" || input.action === "shell") {
      return { reason: "CLI alias read action.", required: false };
    }

    return {
      reason: "CLI alias action writes user shell state.",
      required: true,
    };
  }

  override effectsForInput(input: CliAliasOptions): CapabilityEffect[] {
    if (input.action === "status" || input.action === "shell") {
      return [{ operation: "read", scope: "none" }];
    }

    return [{ operation: "write", scope: "global" }];
  }

  async #remove(): Promise<Result<AgentDevKitErrorCode, CliAliasResult>> {
    const remove = await this.#repository.removeAlias();

    if (remove.isErr()) {
      return Result.fail(remove.unwrapError());
    }

    return this.#view("removed");
  }

  async #set(name: string, force?: boolean): Promise<Result<AgentDevKitErrorCode, CliAliasResult>> {
    const alias = await this.#repository.saveAlias(name, force);

    if (alias.isErr()) {
      return Result.fail(alias.unwrapError());
    }

    return Result.ok(this.#result("configured", alias.unwrap()));
  }

  async #sync(): Promise<Result<AgentDevKitErrorCode, CliAliasResult>> {
    const alias = await this.#repository.syncAlias();

    if (alias.isErr()) {
      return Result.fail(alias.unwrapError());
    }

    return Result.ok(this.#result("configured", alias.unwrap()));
  }

  async #view(
    status: CliAliasResult["status"],
  ): Promise<Result<AgentDevKitErrorCode, CliAliasResult>> {
    const alias = await this.#repository.loadAlias();

    return alias.isOk()
      ? Result.ok(this.#result(status, alias.unwrap()))
      : Result.fail(alias.unwrapError());
  }

  #result(status: CliAliasResult["status"], alias?: CliAliasResult["alias"]): CliAliasResult {
    return {
      activationCommand: this.#repository.activationCommand(),
      alias,
      binDirectory: this.#repository.binDirectory(),
      binDirectoryInPath: this.#repository.binDirectoryInPath(),
      shellCommand: this.#repository.shellCommand(),
      status,
    };
  }
}
