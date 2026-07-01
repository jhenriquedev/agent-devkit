import { BaseCapabilityService, defineCapabilityConfig } from "../../../../infra/bases/capability";
import type { DependencyCheck } from "../../../../infra/bases/dependency";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type DependenciesOptions,
  DependenciesOptionsSchema,
  type DependenciesResult,
  DependenciesResultSchema,
} from "./dependencies.entities";
import type { DependenciesRepositoryPort } from "./dependencies.repository";

type DependenciesServiceDependencies = {
  repository: DependenciesRepositoryPort;
};

export const dependenciesCapabilityConfig = defineCapabilityConfig({
  id: "environment.dependencies",
  moduleId: "environment",
  name: "Environment Dependencies",
  description: "Inspect and plan lifecycle operations for external Agent DevKit dependencies.",
  kind: "deterministic",
  risk: "read-only",
} as const);

function aggregateStatus(statuses: string[]): DependenciesResult["status"] {
  if (statuses.includes("incompatible")) {
    return "incompatible";
  }

  if (statuses.includes("missing")) {
    return "missing";
  }

  if (statuses.includes("unsupported")) {
    return "unsupported";
  }

  if (statuses.includes("warning")) {
    return "warning";
  }

  return "ok";
}

function providerOptions(options: DependenciesOptions) {
  return {
    options: options.options,
    version: options.version,
  };
}

export class DependenciesService extends BaseCapabilityService<
  typeof dependenciesCapabilityConfig,
  DependenciesServiceDependencies
> {
  readonly inputSchema = DependenciesOptionsSchema;
  readonly outputSchema = DependenciesResultSchema;
  readonly #repository: DependenciesRepositoryPort;

  constructor(dependencies: DependenciesServiceDependencies) {
    super(dependenciesCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: DependenciesOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependenciesResult>> {
    if (options.action === "list") {
      return Result.ok({
        action: "list",
        dependencies: this.#repository.listProviders(),
        status: "ok",
      });
    }

    if (
      options.action === "plan-configure" ||
      options.action === "plan-downgrade" ||
      options.action === "plan-install" ||
      options.action === "plan-uninstall" ||
      options.action === "plan-upgrade"
    ) {
      if (options.dependency === undefined) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      const plan = await this.#repository.plan(
        options.dependency,
        options.action,
        providerOptions(options),
      );

      return plan.isOk()
        ? Result.ok({
            action: options.action,
            dependency: options.dependency,
            plan: plan.unwrap(),
            status: plan.unwrap().status,
          })
        : Result.fail(plan.unwrapError());
    }

    if (
      options.action === "configure" ||
      options.action === "downgrade" ||
      options.action === "install" ||
      options.action === "uninstall" ||
      options.action === "upgrade"
    ) {
      if (options.dependency === undefined) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      if (options.confirmed !== true) {
        const planAction = `plan-${options.action}` as
          | "plan-configure"
          | "plan-downgrade"
          | "plan-install"
          | "plan-uninstall"
          | "plan-upgrade";
        const plan = await this.#repository.plan(
          options.dependency,
          planAction,
          providerOptions(options),
        );

        return plan.isOk()
          ? Result.ok({
              action: planAction,
              dependency: options.dependency,
              plan: plan.unwrap(),
              status: plan.unwrap().status,
            })
          : Result.fail(plan.unwrapError());
      }

      const operation = await this.#repository.operation(
        options.dependency,
        options.action,
        providerOptions(options),
      );

      return operation.isOk()
        ? Result.ok({
            action: options.action,
            dependency: options.dependency,
            result: operation.unwrap(),
            status: operation.unwrap().status,
          })
        : Result.fail(operation.unwrapError());
    }

    const checks = await this.#checks(options);

    return checks.isOk()
      ? Result.ok({
          action: options.action,
          checks: checks.unwrap(),
          dependency: options.dependency,
          status: aggregateStatus(checks.unwrap().map((check) => check.status)),
        })
      : Result.fail(checks.unwrapError());
  }

  invoke(options: DependenciesOptions): Promise<Result<AgentDevKitErrorCode, DependenciesResult>> {
    return this.execute(options);
  }

  #checks(options: DependenciesOptions): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    switch (options.action) {
      case "check":
        return this.#repository.check(options.dependency, providerOptions(options));
      case "check-compatibility":
        return this.#repository.checkCompatibility(options.dependency, providerOptions(options));
      case "check-environment":
        return this.#repository.checkEnvironment(options.dependency, providerOptions(options));
      case "check-installed":
        return this.#repository.checkInstalled(options.dependency, providerOptions(options));
      case "verify":
        return this.#repository.verify(options.dependency, providerOptions(options));
      default:
        return Promise.resolve(Result.fail(ErrorCodes.InvalidInput));
    }
  }
}
