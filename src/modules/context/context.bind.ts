import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDataStore } from "../../infra/bases/data_store";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import { LocalAgentDataStore } from "../../infra/data";
import {
  ContextProjectsRepository,
  type ContextProjectsRepositoryPort,
} from "./capabilities/projects/projects.repository";
import { ContextProjectsService } from "./capabilities/projects/projects.service";
import {
  ContextSessionsRepository,
  type ContextSessionsRepositoryPort,
} from "./capabilities/sessions/sessions.repository";
import { ContextSessionsService } from "./capabilities/sessions/sessions.service";
import { contextModuleConfig } from "./context.config";

export type ContextModuleBindOptions = {
  dataStore?: AgentDataStore;
  homeDirectory?: string;
};

export type ContextModuleCapabilities = {
  projects: ContextProjectsService;
  sessions: ContextSessionsService;
};

export type ContextModuleBinding = ModuleBinding<
  typeof contextModuleConfig,
  ContextModuleCapabilities
>;

type ContextModuleBinderDependencies = {
  projectsRepository: (options: ContextModuleBindOptions) => ContextProjectsRepositoryPort;
  sessionsRepository: (options: ContextModuleBindOptions) => ContextSessionsRepositoryPort;
};

const defaultDependencies: ContextModuleBinderDependencies = {
  projectsRepository: (options) => new ContextProjectsRepository(normalizeOptions(options)),
  sessionsRepository: (options) => new ContextSessionsRepository(normalizeOptions(options)),
};

function normalizeOptions(options: ContextModuleBindOptions): ContextModuleBindOptions {
  if (options.dataStore !== undefined || options.homeDirectory === undefined) {
    return options;
  }

  return {
    ...options,
    dataStore: new LocalAgentDataStore({
      rootDirectory: `${options.homeDirectory}/.agent-devkit/data`,
    }),
  };
}

export class ContextModuleBinder extends ModuleBinder<
  ContextModuleBindOptions,
  typeof contextModuleConfig,
  ContextModuleCapabilities
> {
  readonly #dependencies: ContextModuleBinderDependencies;

  constructor(dependencies: ContextModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(
    options: ContextModuleBindOptions = {},
  ): Result<AgentDevKitErrorCode, ContextModuleBinding> {
    return defineModuleBinding({
      config: contextModuleConfig,
      capabilities: {
        projects: new ContextProjectsService({
          repository: this.#dependencies.projectsRepository(options),
        }),
        sessions: new ContextSessionsService({
          repository: this.#dependencies.sessionsRepository(options),
        }),
      },
    });
  }
}

export function createContextModuleBindings(
  options: ContextModuleBindOptions = {},
): Result<AgentDevKitErrorCode, ContextModuleBinding> {
  return new ContextModuleBinder().bind(options);
}
