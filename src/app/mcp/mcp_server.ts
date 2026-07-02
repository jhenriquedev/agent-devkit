import { homedir } from "node:os";
import { join } from "node:path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { AgentRuntime } from "../../infra/agent/agent_runtime";
import type { ToolRuntime } from "../../infra/bases/tool_runtime";
import { createBrainDockProvider } from "../../infra/brain/brain_dock";
import {
  hasObjectOutputSchema,
  inputSchemaWithAgentControl,
  runtimeResultToMcpContent,
  splitMcpToolInput,
} from "./mcp_result_mapper";

const AGENT_TASK_TOOL_NAME = "agent.task";

const agentTaskTool: Tool = {
  name: AGENT_TASK_TOOL_NAME,
  title: "Delegate a task to the local agent",
  description:
    "Delegate a bounded, multi-step or routine local task to the Agent DevKit local agent: it plans and runs the necessary capabilities on your behalf and returns a concise result. Prefer this to offload orchestration and reduce token usage. Use the individual capability tools directly when you need step-by-step control, precise intermediate results, or to intervene mid-task.",
  inputSchema: {
    type: "object",
    properties: {
      approvedTools: {
        type: "array",
        description:
          "Capability ids that are explicitly approved for this run. Approval is scoped per tool call.",
        items: { type: "string" },
      },
      task: {
        type: "string",
        description: "The task to perform, described in natural language.",
      },
    },
    required: ["task"],
  } as Tool["inputSchema"],
  outputSchema: {
    type: "object",
    properties: {
      reply: { type: "string" },
      steps: {
        type: "array",
        items: {
          type: "object",
          properties: {
            ok: { type: "boolean" },
            summary: { type: "string" },
            tool: { type: "string" },
          },
        },
      },
    },
    required: ["reply", "steps"],
  } as Tool["outputSchema"],
  annotations: { openWorldHint: true },
  _meta: { "agent-devkit/kind": "agent-delegation" },
};

export type AgentMcpServerOptions = {
  packageName: string;
  runtime: ToolRuntime;
  version: string;
};

function mcpToolFromRuntimeTool(tool: ReturnType<ToolRuntime["listTools"]>[number]): Tool {
  const mcpTool: Tool = {
    name: tool.id,
    title: tool.name,
    description: tool.description,
    inputSchema: inputSchemaWithAgentControl(tool) as Tool["inputSchema"],
    annotations: {
      destructiveHint: tool.risk === "destructive",
      openWorldHint: tool.risk === "external-write",
      readOnlyHint: tool.risk === "read-only",
    },
    _meta: {
      "agent-devkit/approvalRequired": tool.approval.required,
      "agent-devkit/moduleId": tool.moduleId,
      "agent-devkit/risk": tool.risk,
    },
  };

  if (hasObjectOutputSchema(tool)) {
    return { ...mcpTool, outputSchema: tool.outputSchema as Tool["outputSchema"] };
  }

  return mcpTool;
}

export function createAgentMcpServer(options: AgentMcpServerOptions): Server {
  const server = new Server(
    {
      name: options.packageName,
      version: options.version,
    },
    {
      capabilities: {
        tools: {},
      },
      instructions:
        "Agent DevKit exposes local capabilities as MCP tools, plus an `agent.task` delegation tool. Prefer `agent.task` for bounded, multi-step or routine local tasks to offload orchestration and reduce token usage; use the individual capability tools directly when you need step-by-step control or precise intermediate results. Risky tools require explicit approval through _agent.approved. For agent.task, approval must be scoped with approvedTools.",
    },
  );

  const agent = new AgentRuntime({
    brainProvider: createBrainDockProvider({ stateDirectory: join(homedir(), ".agent-devkit") }),
    toolRuntime: options.runtime,
  });

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [agentTaskTool, ...options.runtime.listTools().map(mcpToolFromRuntimeTool)],
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === AGENT_TASK_TOOL_NAME) {
      const args = (request.params.arguments ?? {}) as Record<string, unknown>;
      const task = typeof args.task === "string" ? args.task : "";
      const approvedTools = Array.isArray(args.approvedTools)
        ? args.approvedTools.filter((tool): tool is string => typeof tool === "string")
        : undefined;

      if (task.length === 0) {
        return { content: [{ type: "text" as const, text: "Missing 'task'." }], isError: true };
      }

      const run = await agent.run({ approvedTools, task });

      if (run.isErr()) {
        return {
          content: [{ type: "text" as const, text: `Agent run failed: ${run.unwrapError()}` }],
          isError: true,
        };
      }

      const payload = run.unwrap();
      const stepsText = payload.steps.map((step) => `- ${step.tool}: ${step.summary}`).join("\n");

      return {
        content: [
          {
            type: "text" as const,
            text: stepsText.length > 0 ? `${payload.reply}\n\nSteps:\n${stepsText}` : payload.reply,
          },
        ],
        isError: false,
        structuredContent: { reply: payload.reply, steps: payload.steps },
      };
    }

    const { approved, capabilityInput } = splitMcpToolInput(request.params.arguments ?? {});
    const result = await options.runtime.execute({
      approved,
      capabilityId: request.params.name,
      input: capabilityInput,
      interface: "mcp",
      requestedBy: "mcp.tools.call",
    });
    const tool = options.runtime.getTool(request.params.name);

    return runtimeResultToMcpContent(result, tool.isOk() && hasObjectOutputSchema(tool.unwrap()));
  });

  return server;
}
