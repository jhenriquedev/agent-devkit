import { describe, expect, it } from "vitest";
import type {
  BrainProviderPort,
  BrainRequest,
  BrainResponse,
  BrainStructuredResponse,
} from "../bases/brain";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";
import type {
  ToolRuntime,
  ToolRuntimeExecuteInput,
  ToolRuntimeResult,
  ToolRuntimeTool,
} from "../bases/tool_runtime";
import { AgentRuntime } from "./agent_runtime";

function demoTool(): ToolRuntimeTool {
  return {
    approval: { reason: "read", required: false },
    description: "Echo tool",
    id: "demo.echo",
    inputSchema: { type: "object" },
    kind: "deterministic",
    moduleId: "demo",
    name: "Echo",
    outputSchema: { type: "object" },
    risk: "read-only",
  };
}

function toolRuntime(overrides: Partial<ToolRuntime> = {}): ToolRuntime {
  const base: ToolRuntime = {
    listTools: () => [demoTool()],
    getTool: () => Result.ok(demoTool()),
    execute: async (input: ToolRuntimeExecuteInput): Promise<ToolRuntimeResult> => ({
      approval: { reason: "read", required: false },
      audit: { durationMs: 0, endedAt: "", startedAt: "" },
      capabilityId: input.capabilityId,
      effects: [],
      input: input.input,
      interface: input.interface,
      output: { echoed: true },
      risk: "read-only",
      status: "succeeded",
    }),
  };

  return { ...base, ...overrides };
}

function brain(decisions: unknown[]): BrainProviderPort {
  let index = 0;

  return {
    generate: async (): Promise<Result<AgentDevKitErrorCode, BrainResponse>> =>
      Result.ok({ schema: "agent-devkit.brain-response/v1", text: "" }),
    generateStructured: async (
      _request: BrainRequest,
      _schema: Record<string, unknown>,
    ): Promise<Result<AgentDevKitErrorCode, BrainStructuredResponse>> => {
      const json = decisions[Math.min(index, decisions.length - 1)];
      index += 1;
      return Result.ok({ json, raw: JSON.stringify(json) });
    },
  };
}

describe("AgentRuntime", () => {
  it("runs a tool then produces a final answer", async () => {
    const runtime = new AgentRuntime({
      brainProvider: brain([
        { action: "tool", input: {}, tool: "demo.echo" },
        { action: "final", reply: "done" },
      ]),
      toolRuntime: toolRuntime(),
    });

    const result = await runtime.run({ task: "echo something" });

    expect(result.isOk()).toBe(true);
    const payload = result.unwrap();
    expect(payload.reply).toBe("done");
    expect(payload.steps).toHaveLength(1);
    expect(payload.steps[0]?.tool).toBe("demo.echo");
    expect(payload.steps[0]?.ok).toBe(true);
  });

  it("stops and reports when a tool requires approval", async () => {
    const runtime = new AgentRuntime({
      brainProvider: brain([{ action: "tool", input: {}, tool: "demo.write" }]),
      toolRuntime: toolRuntime({
        execute: async (input: ToolRuntimeExecuteInput): Promise<ToolRuntimeResult> => ({
          approval: { reason: "write", required: true },
          audit: { durationMs: 0, endedAt: "", startedAt: "" },
          capabilityId: input.capabilityId,
          effects: [],
          error: {
            code: ErrorCodes.ApprovalRequired,
            message: "needs approval",
            recoverable: true,
          },
          input: input.input,
          interface: input.interface,
          risk: "writes-global-state",
          status: "approval_required",
        }),
      }),
    });

    const result = await runtime.run({ task: "write something" });

    expect(result.isOk()).toBe(true);
    expect(result.unwrap().reply).toContain("aprovação");
  });

  it("fails when the provider cannot produce structured output", async () => {
    const runtime = new AgentRuntime({
      brainProvider: {
        generate: async () => Result.ok({ schema: "agent-devkit.brain-response/v1", text: "" }),
      },
      toolRuntime: toolRuntime(),
    });

    const result = await runtime.run({ task: "x" });

    expect(result.isErr()).toBe(true);
    expect(result.unwrapError()).toBe(ErrorCodes.BrainProviderUnavailable);
  });
});
