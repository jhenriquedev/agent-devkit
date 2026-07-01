import type { z } from "zod";
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

export type CapabilityInvocationInterface = "agent" | "cli" | "mcp" | "tui";

export type CapabilityInvocationContext = {
  approved?: boolean;
  correlationId?: string;
  interface: CapabilityInvocationInterface;
  requestedBy?: string;
};

export type CapabilityEffectOperation = "delete" | "external-write" | "read" | "write";

export type CapabilityEffectScope =
  | "external"
  | "global"
  | "none"
  | "project"
  | "project-or-global";

export type CapabilityEffect = {
  operation: CapabilityEffectOperation;
  scope: CapabilityEffectScope;
};

export type CapabilityApproval = {
  reason: string;
  required: boolean;
};

export type CapabilityInvocationAudit = {
  durationMs: number;
  endedAt: string;
  startedAt: string;
};

export type CapabilityInvocationFailure = {
  capabilityId: string;
  audit: CapabilityInvocationAudit;
  error: {
    code: AgentDevKitErrorCode;
    hint?: string;
    message: string;
    recoverable: boolean;
  };
  ok: false;
};

export type CapabilityInvocationSuccess<TOutput = unknown> = {
  capabilityId: string;
  audit: CapabilityInvocationAudit;
  data: TOutput;
  effects: CapabilityEffect[];
  ok: true;
};

export type CapabilityInvocationResult<TOutput = unknown> =
  | CapabilityInvocationFailure
  | CapabilityInvocationSuccess<TOutput>;

export type InvokableCapabilityDescriptor = CapabilityConfig & {
  approval: CapabilityApproval;
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
};

export type InvokableCapabilityService<TInput = unknown, TOutput = unknown> = BaseCapabilityService<
  CapabilityConfig,
  unknown,
  TInput,
  TOutput
>;

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

export abstract class BaseCapabilityService<
  TConfig extends CapabilityConfig,
  TDependencies,
  TInput = unknown,
  TOutput = unknown,
> {
  readonly capability: TConfig;
  abstract readonly inputSchema: z.ZodType<TInput>;
  abstract readonly outputSchema: z.ZodType<TOutput>;
  protected readonly dependencies: TDependencies;

  protected constructor(capability: TConfig, dependencies: TDependencies) {
    this.capability = capability;
    this.dependencies = dependencies;
  }

  abstract invoke(
    input: TInput,
    context: CapabilityInvocationContext,
  ): Promise<Result<AgentDevKitErrorCode, TOutput>>;

  approvalForInput?(input: TInput, context: CapabilityInvocationContext): CapabilityApproval;

  effectsForInput?(input: TInput, context: CapabilityInvocationContext): CapabilityEffect[];
}

export function defineCapabilityConfig<TConfig extends CapabilityConfig>(config: TConfig): TConfig {
  return config;
}
