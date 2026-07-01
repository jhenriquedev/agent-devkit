import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  ModelsRegistryRepository,
  type ModelsRegistryRepositoryPort,
} from "./capabilities/registry/registry.repository";
import { ModelsRegistryService } from "./capabilities/registry/registry.service";
import { modelsModuleConfig } from "./models.config";

export type ModelsModuleBindOptions = {
  homeDirectory?: string;
  stateDirectory?: string;
};

export type ModelsModuleCapabilities = {
  registry: ModelsRegistryService;
};

export type ModelsModuleBinding = ModuleBinding<
  typeof modelsModuleConfig,
  ModelsModuleCapabilities
>;

type ModelsModuleBinderDependencies = {
  registryRepository: (options: ModelsModuleBindOptions) => ModelsRegistryRepositoryPort;
};

function stateDirectory(options: ModelsModuleBindOptions): string | undefined {
  return (
    options.stateDirectory ??
    (options.homeDirectory ? `${options.homeDirectory}/.agent-devkit` : undefined)
  );
}

const defaultDependencies: ModelsModuleBinderDependencies = {
  registryRepository: (options) =>
    new ModelsRegistryRepository({ stateDirectory: stateDirectory(options) }),
};

export class ModelsModuleBinder extends ModuleBinder<
  ModelsModuleBindOptions,
  typeof modelsModuleConfig,
  ModelsModuleCapabilities
> {
  readonly #dependencies: ModelsModuleBinderDependencies;

  constructor(dependencies: ModelsModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(
    options: ModelsModuleBindOptions = {},
  ): Result<AgentDevKitErrorCode, ModelsModuleBinding> {
    return defineModuleBinding({
      config: modelsModuleConfig,
      capabilities: {
        registry: new ModelsRegistryService({
          repository: this.#dependencies.registryRepository(options),
        }),
      },
    });
  }
}

export function createModelsModuleBindings(
  options: ModelsModuleBindOptions = {},
): Result<AgentDevKitErrorCode, ModelsModuleBinding> {
  return new ModelsModuleBinder().bind(options);
}
