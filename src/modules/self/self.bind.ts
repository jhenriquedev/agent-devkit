import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  UpdateRepository,
  type UpdateRepositoryPort,
} from "./capabilities/update/update.repository";
import { UpdateService } from "./capabilities/update/update.service";
import { selfModuleConfig } from "./self.config";

export type SelfModuleBindOptions = {
  currentVersion: string;
  packageName: string;
};

export type SelfModuleCapabilities = {
  update: UpdateService;
};

export type SelfModuleBinding = ModuleBinding<typeof selfModuleConfig, SelfModuleCapabilities>;

type SelfModuleBinderDependencies = {
  updateRepository: () => UpdateRepositoryPort;
};

const defaultDependencies: SelfModuleBinderDependencies = {
  updateRepository: () => new UpdateRepository(),
};

export class SelfModuleBinder extends ModuleBinder<
  SelfModuleBindOptions,
  typeof selfModuleConfig,
  SelfModuleCapabilities
> {
  readonly #dependencies: SelfModuleBinderDependencies;

  constructor(dependencies: SelfModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(options: SelfModuleBindOptions): Result<AgentDevKitErrorCode, SelfModuleBinding> {
    return defineModuleBinding({
      config: selfModuleConfig,
      capabilities: {
        update: new UpdateService({
          currentVersion: options.currentVersion,
          packageName: options.packageName,
          repository: this.#dependencies.updateRepository(),
        }),
      },
    });
  }
}

export function createSelfModuleBindings(
  options: SelfModuleBindOptions,
): Result<AgentDevKitErrorCode, SelfModuleBinding> {
  return new SelfModuleBinder().bind(options);
}
