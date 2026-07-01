import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  DependenciesRepository,
  type DependenciesRepositoryPort,
} from "./capabilities/dependencies/dependencies.repository";
import { DependenciesService } from "./capabilities/dependencies/dependencies.service";
import { environmentModuleConfig } from "./environment.config";

export type EnvironmentModuleBindOptions = Record<string, never>;

export type EnvironmentModuleCapabilities = {
  dependencies: DependenciesService;
};

export type EnvironmentModuleBinding = ModuleBinding<
  typeof environmentModuleConfig,
  EnvironmentModuleCapabilities
>;

type EnvironmentModuleBinderDependencies = {
  dependenciesRepository: () => DependenciesRepositoryPort;
};

const defaultDependencies: EnvironmentModuleBinderDependencies = {
  dependenciesRepository: () => new DependenciesRepository(),
};

export class EnvironmentModuleBinder extends ModuleBinder<
  EnvironmentModuleBindOptions,
  typeof environmentModuleConfig,
  EnvironmentModuleCapabilities
> {
  readonly #dependencies: EnvironmentModuleBinderDependencies;

  constructor(dependencies: EnvironmentModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(
    _options: EnvironmentModuleBindOptions = {},
  ): Result<AgentDevKitErrorCode, EnvironmentModuleBinding> {
    return defineModuleBinding({
      config: environmentModuleConfig,
      capabilities: {
        dependencies: new DependenciesService({
          repository: this.#dependencies.dependenciesRepository(),
        }),
      },
    });
  }
}

export function createEnvironmentModuleBindings(
  options: EnvironmentModuleBindOptions = {},
): Result<AgentDevKitErrorCode, EnvironmentModuleBinding> {
  return new EnvironmentModuleBinder().bind(options);
}
