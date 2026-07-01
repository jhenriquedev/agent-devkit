import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  CliAliasRepository,
  type CliAliasRepositoryPort,
} from "./capabilities/cliAlias/cliAlias.repository";
import { CliAliasService } from "./capabilities/cliAlias/cliAlias.service";
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
  cliAlias: CliAliasService;
  personalization: PersonalizationService;
  preferences: PreferencesService;
};

export type UserModuleBinding = ModuleBinding<typeof userModuleConfig, UserModuleCapabilities>;

type UserModuleBinderDependencies = {
  cliAliasRepository: (options: UserModuleBindOptions) => CliAliasRepositoryPort;
  personalizationRepository: (options: UserModuleBindOptions) => PersonalizationRepositoryPort;
  preferencesRepository: (options: UserModuleBindOptions) => PreferencesRepositoryPort;
};

const defaultDependencies: UserModuleBinderDependencies = {
  cliAliasRepository: (options) =>
    new CliAliasRepository({
      homeDirectory: options.homeDirectory,
      preferencesRepository: new PreferencesRepository(options),
    }),
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
        cliAlias: new CliAliasService({
          repository: this.#dependencies.cliAliasRepository(options),
        }),
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
