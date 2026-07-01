import type { ToolRuntime, ToolRuntimeResult } from "../../infra/bases/tool_runtime";

export type AgentMcpTool = {
  description: string;
  inputSchema: Record<string, unknown>;
  name: string;
};

export type AgentMcpAdapterOptions = {
  runtime: ToolRuntime;
};

export class AgentMcpAdapter {
  readonly #runtime: ToolRuntime;

  constructor(options: AgentMcpAdapterOptions) {
    this.#runtime = options.runtime;
  }

  listTools(): AgentMcpTool[] {
    return this.#runtime.listTools().map((tool) => ({
      description: tool.description,
      inputSchema: tool.inputSchema,
      name: tool.id,
    }));
  }

  callTool(
    name: string,
    input: unknown,
    context: { approved?: boolean; requestedBy?: string } = {},
  ): Promise<ToolRuntimeResult> {
    return this.#runtime.execute({
      approved: context.approved,
      capabilityId: name,
      input,
      interface: "mcp",
      requestedBy: context.requestedBy,
    });
  }
}
