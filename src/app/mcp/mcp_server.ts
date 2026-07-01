import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";
import type { ToolRuntime } from "../../infra/bases/tool_runtime";
import {
  inputSchemaWithAgentControl,
  runtimeResultToMcpContent,
  splitMcpToolInput,
} from "./mcp_result_mapper";

export type AgentMcpServerOptions = {
  packageName: string;
  runtime: ToolRuntime;
  version: string;
};

function mcpToolFromRuntimeTool(tool: ReturnType<ToolRuntime["listTools"]>[number]): Tool {
  return {
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
        "Agent DevKit exposes local capabilities as MCP tools. Risky tools require explicit approval through _agent.approved.",
    },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: options.runtime.listTools().map(mcpToolFromRuntimeTool),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { approved, capabilityInput } = splitMcpToolInput(request.params.arguments ?? {});
    const result = await options.runtime.execute({
      approved,
      capabilityId: request.params.name,
      input: capabilityInput,
      interface: "mcp",
      requestedBy: "mcp.tools.call",
    });

    return runtimeResultToMcpContent(result);
  });

  return server;
}
