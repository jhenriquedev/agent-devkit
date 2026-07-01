import type {
  CapabilityApproval,
  CapabilityEffect,
  CapabilityInvocationAudit,
  CapabilityInvocationInterface,
  CapabilityKind,
  CapabilityRisk,
} from "./capability";
import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type ToolRuntimeTool = {
  approval: CapabilityApproval;
  description: string;
  id: string;
  inputSchema: Record<string, unknown>;
  kind: CapabilityKind;
  moduleId: string;
  name: string;
  outputSchema: Record<string, unknown>;
  risk: CapabilityRisk;
};

export type ToolRuntimeExecuteInput = {
  approved?: boolean;
  capabilityId: string;
  input: unknown;
  interface: CapabilityInvocationInterface;
  requestedBy?: string;
};

export type ToolRuntimeResultStatus = "approval_required" | "failed" | "succeeded";

export type ToolRuntimeResult = {
  approval: CapabilityApproval;
  audit: CapabilityInvocationAudit;
  capabilityId: string;
  effects: CapabilityEffect[];
  error?: {
    code: AgentDevKitErrorCode;
    hint?: string;
    message: string;
    recoverable: boolean;
  };
  input: unknown;
  interface: CapabilityInvocationInterface;
  output?: unknown;
  risk: CapabilityRisk;
  status: ToolRuntimeResultStatus;
};

export interface ToolRuntime {
  execute(input: ToolRuntimeExecuteInput): Promise<ToolRuntimeResult>;
  getTool(capabilityId: string): Result<AgentDevKitErrorCode, ToolRuntimeTool>;
  listTools(): ToolRuntimeTool[];
}
