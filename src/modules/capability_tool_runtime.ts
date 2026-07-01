import { type AgentDevKitErrorCode, ErrorCodes } from "../infra/bases/errors";
import type { Result } from "../infra/bases/result";
import type {
  ToolRuntime,
  ToolRuntimeExecuteInput,
  ToolRuntimeResult,
  ToolRuntimeTool,
} from "../infra/bases/tool_runtime";
import type { CapabilityRegistry } from "../infra/capabilities/capability_registry";
import {
  type AgentCapabilityRegistryOptions,
  createAgentCapabilityRegistry,
} from "./capability_registry";

export type CapabilityToolRuntimeOptions = {
  registry: CapabilityRegistry;
};

function toolFromDescriptor(
  descriptor: ReturnType<CapabilityRegistry["list"]>[number],
): ToolRuntimeTool {
  return {
    approval: descriptor.approval,
    description: descriptor.description,
    id: descriptor.id,
    inputSchema: descriptor.inputSchema,
    kind: descriptor.kind,
    moduleId: descriptor.moduleId,
    name: descriptor.name,
    outputSchema: descriptor.outputSchema,
    risk: descriptor.risk,
  };
}

export class CapabilityToolRuntime implements ToolRuntime {
  readonly #registry: CapabilityRegistry;

  constructor(options: CapabilityToolRuntimeOptions) {
    this.#registry = options.registry;
  }

  listTools(): ToolRuntimeTool[] {
    return this.#registry.list().map(toolFromDescriptor);
  }

  getTool(capabilityId: string): Result<AgentDevKitErrorCode, ToolRuntimeTool> {
    return this.#registry.describe(capabilityId).map(toolFromDescriptor);
  }

  async execute(input: ToolRuntimeExecuteInput): Promise<ToolRuntimeResult> {
    const tool = this.getTool(input.capabilityId);
    const invocation = await this.#registry.invoke(input.capabilityId, input.input, {
      approved: input.approved,
      interface: input.interface,
      requestedBy: input.requestedBy,
    });

    if (tool.isErr()) {
      return {
        approval: { reason: "Capability was not found.", required: false },
        audit: invocation.audit,
        capabilityId: input.capabilityId,
        effects: [],
        error: invocation.ok
          ? {
              code: ErrorCodes.CapabilityNotFound,
              message: `Capability ${input.capabilityId} was not found.`,
              recoverable: true,
            }
          : invocation.error,
        input: input.input,
        interface: input.interface,
        risk: "read-only",
        status: "failed",
      };
    }

    const descriptor = tool.unwrap();

    if (!invocation.ok) {
      return {
        approval: descriptor.approval,
        audit: invocation.audit,
        capabilityId: input.capabilityId,
        effects: [],
        error: invocation.error,
        input: input.input,
        interface: input.interface,
        risk: descriptor.risk,
        status:
          invocation.error.code === ErrorCodes.ApprovalRequired ? "approval_required" : "failed",
      };
    }

    return {
      approval: descriptor.approval,
      audit: invocation.audit,
      capabilityId: input.capabilityId,
      effects: invocation.effects,
      input: input.input,
      interface: input.interface,
      output: invocation.data,
      risk: descriptor.risk,
      status: "succeeded",
    };
  }
}

export function createCapabilityToolRuntime(
  options: AgentCapabilityRegistryOptions,
): Result<AgentDevKitErrorCode, CapabilityToolRuntime> {
  return createAgentCapabilityRegistry(options).map(
    (registry) => new CapabilityToolRuntime({ registry }),
  );
}
