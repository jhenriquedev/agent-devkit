import { BaseCapabilityService, defineCapabilityConfig } from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import type { SecretsVaultOptions, SecretsVaultResult, SecretView } from "./vault.entities";
import type { SecretsVaultRepositoryPort } from "./vault.repository";

type SecretsVaultServiceDependencies = {
  repository: SecretsVaultRepositoryPort;
};

export const secretsVaultCapabilityConfig = defineCapabilityConfig({
  id: "secrets.vault",
  moduleId: "secrets",
  name: "Secrets Vault",
  description: "Store and retrieve encrypted local credentials.",
  kind: "deterministic",
  risk: "writes-global-state",
} as const);

function masked(summary: Omit<SecretView, "value">): SecretView {
  return {
    ...summary,
    value: "********",
  };
}

export class SecretsVaultService extends BaseCapabilityService<
  typeof secretsVaultCapabilityConfig,
  SecretsVaultServiceDependencies
> {
  readonly #repository: SecretsVaultRepositoryPort;

  constructor(dependencies: SecretsVaultServiceDependencies) {
    super(secretsVaultCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: SecretsVaultOptions,
  ): Promise<Result<AgentDevKitErrorCode, SecretsVaultResult>> {
    if (options.action === "list") {
      const secrets = await this.#repository.list();

      return secrets.isOk()
        ? Result.ok({
            action: "list",
            path: this.#repository.path(),
            secrets: secrets.unwrap().map((secret) => masked(secret)),
          })
        : Result.fail(secrets.unwrapError());
    }

    if (options.action === "set") {
      const secret = await this.#repository.set(options.name, options.value, {
        service: options.service,
      });

      return secret.isOk()
        ? Result.ok({
            action: "set",
            path: this.#repository.path(),
            secret: masked(secret.unwrap()),
          })
        : Result.fail(secret.unwrapError());
    }

    if (options.action === "remove") {
      const removed = await this.#repository.remove(options.name);

      return removed.isOk()
        ? Result.ok({
            action: "remove",
            path: this.#repository.path(),
            removed: removed.unwrap().removed,
            secret: { name: options.name },
          })
        : Result.fail(removed.unwrapError());
    }

    const summaries = await this.#repository.list();

    if (summaries.isErr()) {
      return Result.fail(summaries.unwrapError());
    }

    const summary = summaries.unwrap().find((secret) => secret.name === options.name);

    if (summary === undefined) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    if (options.reveal === true) {
      const value = await this.#repository.get(options.name);

      return value.isOk()
        ? Result.ok({
            action: "show",
            path: this.#repository.path(),
            secret: { ...summary, value: value.unwrap() },
          })
        : Result.fail(value.unwrapError());
    }

    return Result.ok({
      action: "show",
      path: this.#repository.path(),
      secret: masked(summary),
    });
  }
}
