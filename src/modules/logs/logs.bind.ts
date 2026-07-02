import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import {
  LogsAnalysisRepository,
  type LogsAnalysisRepositoryPort,
} from "./capabilities/analysis/analysis.repository";
import { LogsAnalysisService } from "./capabilities/analysis/analysis.service";
import { logsModuleConfig } from "./logs.config";

export type LogsModuleBindOptions = {
  homeDirectory?: string;
  stateDirectory?: string;
};

export type LogsModuleCapabilities = {
  analysis: LogsAnalysisService;
};

export type LogsModuleBinding = ModuleBinding<typeof logsModuleConfig, LogsModuleCapabilities>;

type LogsModuleBinderDependencies = {
  analysisRepository: (options: LogsModuleBindOptions) => LogsAnalysisRepositoryPort;
};

const defaultDependencies: LogsModuleBinderDependencies = {
  analysisRepository: (options) => new LogsAnalysisRepository(options),
};

export class LogsModuleBinder extends ModuleBinder<
  LogsModuleBindOptions,
  typeof logsModuleConfig,
  LogsModuleCapabilities
> {
  readonly #dependencies: LogsModuleBinderDependencies;

  constructor(dependencies: LogsModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(options: LogsModuleBindOptions): Result<AgentDevKitErrorCode, LogsModuleBinding> {
    return defineModuleBinding({
      config: logsModuleConfig,
      capabilities: {
        analysis: new LogsAnalysisService({
          repository: this.#dependencies.analysisRepository(options),
        }),
      },
    });
  }
}

export function createLogsModuleBindings(
  options: LogsModuleBindOptions = {},
): Result<AgentDevKitErrorCode, LogsModuleBinding> {
  return new LogsModuleBinder().bind(options);
}
