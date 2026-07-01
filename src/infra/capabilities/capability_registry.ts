import { z } from "zod";
import type {
  CapabilityApproval,
  CapabilityEffect,
  CapabilityInvocationAudit,
  CapabilityInvocationContext,
  CapabilityInvocationFailure,
  CapabilityInvocationResult,
  InvokableCapabilityDescriptor,
  InvokableCapabilityService,
} from "../bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export type CapabilityRegistryOptions = {
  capabilities: InvokableCapabilityService[];
  clock?: () => Date;
};

function effectsFor(capability: InvokableCapabilityService): CapabilityEffect[] {
  switch (capability.capability.risk) {
    case "destructive":
      return [{ operation: "delete", scope: "project-or-global" }];
    case "external-write":
      return [{ operation: "external-write", scope: "external" }];
    case "read-only":
      return [{ operation: "read", scope: "none" }];
    case "writes-global-state":
      return [{ operation: "write", scope: "global" }];
    case "writes-project-state":
      return [{ operation: "write", scope: "project" }];
  }
}

function approvalFor(capability: InvokableCapabilityService): CapabilityApproval {
  switch (capability.capability.risk) {
    case "destructive":
      return {
        reason: "Capability can remove state and requires explicit approval.",
        required: true,
      };
    case "external-write":
      return {
        reason: "Capability writes to an external system.",
        required: true,
      };
    case "read-only":
      return {
        reason: "Capability is read-only.",
        required: false,
      };
    case "writes-global-state":
      return {
        reason: "Capability writes global state.",
        required: true,
      };
    case "writes-project-state":
      return {
        reason: "Capability writes project state.",
        required: true,
      };
  }
}

function audit(startedAt: Date, endedAt: Date): CapabilityInvocationAudit {
  return {
    durationMs: Math.max(0, endedAt.getTime() - startedAt.getTime()),
    endedAt: endedAt.toISOString(),
    startedAt: startedAt.toISOString(),
  };
}

function failure(
  capabilityId: string,
  auditPayload: CapabilityInvocationAudit,
  code: CapabilityInvocationFailure["error"]["code"],
  message: string,
  hint?: string,
): CapabilityInvocationFailure {
  return {
    audit: auditPayload,
    capabilityId,
    error: {
      code,
      hint,
      message,
      recoverable: code === ErrorCodes.InvalidInput || code === ErrorCodes.CapabilityNotFound,
    },
    ok: false,
  };
}

export class CapabilityRegistry {
  readonly #capabilities: Map<string, InvokableCapabilityService>;
  readonly #clock: () => Date;

  constructor(options: CapabilityRegistryOptions) {
    this.#clock = options.clock ?? (() => new Date());
    this.#capabilities = new Map(
      options.capabilities.map((capability) => [capability.capability.id, capability]),
    );
  }

  describe(id: string): Result<AgentDevKitErrorCode, InvokableCapabilityDescriptor> {
    const capability = this.#capabilities.get(id);

    if (capability === undefined) {
      return Result.fail(ErrorCodes.CapabilityNotFound);
    }

    return Result.ok(this.#descriptor(capability));
  }

  list(): InvokableCapabilityDescriptor[] {
    return [...this.#capabilities.values()]
      .map((capability) => this.#descriptor(capability))
      .sort((left, right) => left.id.localeCompare(right.id));
  }

  async invoke(
    capabilityId: string,
    input: unknown,
    context: CapabilityInvocationContext,
  ): Promise<CapabilityInvocationResult> {
    const startedAt = this.#clock();
    const capability = this.#capabilities.get(capabilityId);

    if (capability === undefined) {
      const endedAt = this.#clock();
      return failure(
        capabilityId,
        audit(startedAt, endedAt),
        ErrorCodes.CapabilityNotFound,
        `Capability ${capabilityId} was not found.`,
      );
    }

    const parsed = capability.inputSchema.safeParse(input);

    if (!parsed.success) {
      const endedAt = this.#clock();
      return failure(
        capabilityId,
        audit(startedAt, endedAt),
        ErrorCodes.InvalidInput,
        "Capability input did not match the declared schema.",
        z.prettifyError(parsed.error),
      );
    }

    const result = await capability.invoke(parsed.data, context);
    const endedAt = this.#clock();
    const auditPayload = audit(startedAt, endedAt);

    if (result.isErr()) {
      return failure(
        capabilityId,
        auditPayload,
        result.unwrapError(),
        `Capability ${capabilityId} failed.`,
      );
    }

    const output = capability.outputSchema.safeParse(result.unwrap());

    if (!output.success) {
      return failure(
        capabilityId,
        auditPayload,
        ErrorCodes.CapabilityExecutionFailed,
        "Capability output did not match the declared schema.",
        z.prettifyError(output.error),
      );
    }

    return {
      audit: auditPayload,
      capabilityId,
      data: output.data,
      effects: effectsFor(capability),
      ok: true,
    };
  }

  #descriptor(capability: InvokableCapabilityService): InvokableCapabilityDescriptor {
    return {
      ...capability.capability,
      approval: approvalFor(capability),
      inputSchema: z.toJSONSchema(capability.inputSchema) as Record<string, unknown>,
      outputSchema: z.toJSONSchema(capability.outputSchema) as Record<string, unknown>,
    };
  }
}

export function createCapabilityRegistry(
  options: CapabilityRegistryOptions,
): Result<AgentDevKitErrorCode, CapabilityRegistry> {
  const seen = new Set<string>();

  for (const capability of options.capabilities) {
    if (seen.has(capability.capability.id)) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    seen.add(capability.capability.id);
  }

  return Result.ok(new CapabilityRegistry(options));
}
