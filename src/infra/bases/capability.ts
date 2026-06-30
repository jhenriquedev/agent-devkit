import type { AgentDevKitConfig } from "./config";
import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type CapabilityKind = "brain-assisted" | "composite" | "deterministic" | "external";

export type CapabilityRisk =
  | "destructive"
  | "external-write"
  | "read-only"
  | "writes-global-state"
  | "writes-project-state";

export type CapabilityConfig = AgentDevKitConfig & {
  readonly kind: CapabilityKind;
  readonly moduleId: string;
  readonly risk: CapabilityRisk;
};

export type CapabilityRepositoryPort = {
  readonly repositoryId: string;
};

export type CapabilityExecution<
  TInput,
  TOutput,
  TError extends string = AgentDevKitErrorCode,
> = TInput extends void
  ? {
      execute(): Promise<Result<TError, TOutput>>;
    }
  : {
      execute(input: TInput): Promise<Result<TError, TOutput>>;
    };

export abstract class BaseCapabilityService<TConfig extends CapabilityConfig, TDependencies> {
  readonly capability: TConfig;
  protected readonly dependencies: TDependencies;

  protected constructor(capability: TConfig, dependencies: TDependencies) {
    this.capability = capability;
    this.dependencies = dependencies;
  }
}

export function defineCapabilityConfig<TConfig extends CapabilityConfig>(config: TConfig): TConfig {
  return config;
}
