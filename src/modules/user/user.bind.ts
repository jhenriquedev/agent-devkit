import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  PersonalizationRepository,
  type PersonalizationRepositoryPort,
} from "./capabilities/personalization/personalization.repository";
import { PersonalizationService } from "./capabilities/personalization/personalization.service";
import {
  PreferencesRepository,
  type PreferencesRepositoryPort,
} from "./capabilities/preferences/preferences.repository";
import { PreferencesService } from "./capabilities/preferences/preferences.service";
import { userModuleConfig } from "./user.config";

export type UserModuleBindOptions = {
  homeDirectory?: string;
};

export type UserModuleCapabilities = {
  personalization: PersonalizationService;
  preferences: PreferencesService;
};

export type UserModuleBinding = ModuleBinding<typeof userModuleConfig, UserModuleCapabilities>;

type UserModuleBinderDependencies = {
  personalizationRepository: (options: UserModuleBindOptions) => PersonalizationRepositoryPort;
  preferencesRepository: (options: UserModuleBindOptions) => PreferencesRepositoryPort;
};

const defaultDependencies: UserModuleBinderDependencies = {
  personalizationRepository: (options) => new PersonalizationRepository(options),
  preferencesRepository: (options) => new PreferencesRepository(options),
};

export class UserModuleBinder extends ModuleBinder<
  UserModuleBindOptions,
  typeof userModuleConfig,
  UserModuleCapabilities
> {
  readonly #dependencies: UserModuleBinderDependencies;

  constructor(dependencies: UserModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(options: UserModuleBindOptions): Result<AgentDevKitErrorCode, UserModuleBinding> {
    return defineModuleBinding({
      config: userModuleConfig,
      capabilities: {
        personalization: new PersonalizationService({
          repository: this.#dependencies.personalizationRepository(options),
        }),
        preferences: new PreferencesService({
          repository: this.#dependencies.preferencesRepository(options),
        }),
      },
    });
  }
}

export function createUserModuleBindings(
  options: UserModuleBindOptions = {},
): Result<AgentDevKitErrorCode, UserModuleBinding> {
  return new UserModuleBinder().bind(options);
}
