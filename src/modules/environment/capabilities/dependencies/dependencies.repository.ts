import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type {
  DependencyCheck,
  DependencyMetadata,
  DependencyOperationResult,
  DependencyPlan,
  DependencyProvider,
  DependencyProviderOptions,
} from "../../../../infra/bases/dependency";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { NodeDependencyProvider } from "./providers/node.provider";

export interface DependenciesRepositoryPort extends CapabilityRepositoryPort {
  check(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>>;
  checkCompatibility(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>>;
  checkEnvironment(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>>;
  checkInstalled(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>>;
  listProviders(): DependencyMetadata[];
  operation(
    dependency: string,
    action: "configure" | "downgrade" | "install" | "uninstall" | "upgrade",
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>>;
  plan(
    dependency: string,
    action:
      | "plan-configure"
      | "plan-downgrade"
      | "plan-install"
      | "plan-uninstall"
      | "plan-upgrade",
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>>;
  verify(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>>;
}

export type DependenciesRepositoryOptions = {
  providers?: DependencyProvider[];
};

const defaultProviders = [new NodeDependencyProvider()];

async function collectChecks(
  providers: DependencyProvider[],
  mapper: (provider: DependencyProvider) => Promise<Result<AgentDevKitErrorCode, DependencyCheck>>,
): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
  const checks: DependencyCheck[] = [];

  for (const provider of providers) {
    const result = await mapper(provider);

    if (result.isErr()) {
      return Result.fail(result.unwrapError());
    }

    checks.push(result.unwrap());
  }

  return Result.ok(checks);
}

export class DependenciesRepository implements DependenciesRepositoryPort {
  readonly repositoryId = "environment.dependencies.repository";
  readonly #providers: Map<string, DependencyProvider>;

  constructor(options: DependenciesRepositoryOptions = {}) {
    this.#providers = new Map(
      (options.providers ?? defaultProviders).map((provider) => [provider.metadata().id, provider]),
    );
  }

  listProviders(): DependencyMetadata[] {
    return [...this.#providers.values()]
      .map((provider) => provider.metadata())
      .sort((left, right) => left.id.localeCompare(right.id));
  }

  check(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    return this.#runChecks(dependency, (provider) => provider.verify(options));
  }

  checkCompatibility(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    return this.#runChecks(dependency, (provider) => provider.checkCompatibility(options));
  }

  checkEnvironment(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    return this.#runChecks(dependency, (provider) => provider.checkEnvironment(options));
  }

  checkInstalled(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    return this.#runChecks(dependency, (provider) => provider.checkInstalled(options));
  }

  operation(
    dependency: string,
    action: "configure" | "downgrade" | "install" | "uninstall" | "upgrade",
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyOperationResult>> {
    const provider = this.#provider(dependency);

    if (provider.isErr()) {
      return Promise.resolve(Result.fail(provider.unwrapError()));
    }

    switch (action) {
      case "configure":
        return provider.unwrap().configure(options);
      case "downgrade":
        return provider.unwrap().downgrade(options);
      case "install":
        return provider.unwrap().install(options);
      case "uninstall":
        return provider.unwrap().uninstall(options);
      case "upgrade":
        return provider.unwrap().upgrade(options);
    }
  }

  plan(
    dependency: string,
    action:
      | "plan-configure"
      | "plan-downgrade"
      | "plan-install"
      | "plan-uninstall"
      | "plan-upgrade",
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyPlan>> {
    const provider = this.#provider(dependency);

    if (provider.isErr()) {
      return Promise.resolve(Result.fail(provider.unwrapError()));
    }

    switch (action) {
      case "plan-configure":
        return provider.unwrap().planConfigure(options);
      case "plan-downgrade":
        return provider.unwrap().planDowngrade(options);
      case "plan-install":
        return provider.unwrap().planInstall(options);
      case "plan-uninstall":
        return provider.unwrap().planUninstall(options);
      case "plan-upgrade":
        return provider.unwrap().planUpgrade(options);
    }
  }

  verify(
    dependency: string | undefined,
    options?: DependencyProviderOptions,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    return this.#runChecks(dependency, (provider) => provider.verify(options));
  }

  #provider(id: string): Result<AgentDevKitErrorCode, DependencyProvider> {
    const provider = this.#providers.get(id);
    return provider === undefined ? Result.fail(ErrorCodes.InvalidInput) : Result.ok(provider);
  }

  #selectedProviders(
    dependency: string | undefined,
  ): Result<AgentDevKitErrorCode, DependencyProvider[]> {
    if (dependency === undefined) {
      return Result.ok([...this.#providers.values()]);
    }

    return this.#provider(dependency).map((provider) => [provider]);
  }

  async #runChecks(
    dependency: string | undefined,
    mapper: (
      provider: DependencyProvider,
    ) => Promise<Result<AgentDevKitErrorCode, DependencyCheck>>,
  ): Promise<Result<AgentDevKitErrorCode, DependencyCheck[]>> {
    const providers = this.#selectedProviders(dependency);

    if (providers.isErr()) {
      return Result.fail(providers.unwrapError());
    }

    return collectChecks(providers.unwrap(), mapper);
  }
}
