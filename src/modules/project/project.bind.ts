import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  DoctorRepository,
  type DoctorRepositoryPort,
} from "./capabilities/doctor/doctor.repository";
import { DoctorService } from "./capabilities/doctor/doctor.service";
import { InitRepository, type InitRepositoryPort } from "./capabilities/init/init.repository";
import { InitService } from "./capabilities/init/init.service";
import { ResetRepository, type ResetRepositoryPort } from "./capabilities/reset/reset.repository";
import { ResetService } from "./capabilities/reset/reset.service";
import { projectModuleConfig } from "./project.config";

export type ProjectModuleBindOptions = {
  appVersion: string;
};

export type ProjectModuleCapabilities = {
  doctor: DoctorService;
  init: InitService;
  reset: ResetService;
};

export type ProjectModuleBinding = ModuleBinding<
  typeof projectModuleConfig,
  ProjectModuleCapabilities
>;

type ProjectModuleBinderDependencies = {
  doctorRepository: () => DoctorRepositoryPort;
  initRepository: () => InitRepositoryPort;
  resetRepository: () => ResetRepositoryPort;
};

const defaultDependencies: ProjectModuleBinderDependencies = {
  doctorRepository: () => new DoctorRepository(),
  initRepository: () => new InitRepository(),
  resetRepository: () => new ResetRepository(),
};

export class ProjectModuleBinder extends ModuleBinder<
  ProjectModuleBindOptions,
  typeof projectModuleConfig,
  ProjectModuleCapabilities
> {
  readonly #dependencies: ProjectModuleBinderDependencies;

  constructor(dependencies: ProjectModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(
    options: ProjectModuleBindOptions,
  ): Result<AgentDevKitErrorCode, ProjectModuleBinding> {
    return defineModuleBinding({
      config: projectModuleConfig,
      capabilities: {
        doctor: new DoctorService({
          appVersion: options.appVersion,
          repository: this.#dependencies.doctorRepository(),
        }),
        init: new InitService({
          appVersion: options.appVersion,
          repository: this.#dependencies.initRepository(),
        }),
        reset: new ResetService({
          repository: this.#dependencies.resetRepository(),
        }),
      },
    });
  }
}

export function createProjectModuleBindings(
  options: ProjectModuleBindOptions,
): Result<AgentDevKitErrorCode, ProjectModuleBinding> {
  return new ProjectModuleBinder().bind(options);
}
