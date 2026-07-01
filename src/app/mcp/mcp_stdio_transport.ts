import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { ToolRuntime } from "../../infra/bases/tool_runtime";
import { createAgentMcpServer } from "./mcp_server";

export type StartMcpStdioServerOptions = {
  packageName: string;
  runtime: ToolRuntime;
  version: string;
};

export async function startMcpStdioServer(options: StartMcpStdioServerOptions): Promise<void> {
  const server = createAgentMcpServer(options);
  const transport = new StdioServerTransport();

  await server.connect(transport);
}
