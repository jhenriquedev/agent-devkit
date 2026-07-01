import type { CapabilityInvocationResult } from "../../infra/bases/capability";
import type { CapabilityRegistry } from "../../infra/capabilities/capability_registry";

export type AgentMcpTool = {
  description: string;
  inputSchema: Record<string, unknown>;
  name: string;
};

export type AgentMcpAdapterOptions = {
  registry: CapabilityRegistry;
};

export class AgentMcpAdapter {
  readonly #registry: CapabilityRegistry;

  constructor(options: AgentMcpAdapterOptions) {
    this.#registry = options.registry;
  }

  listTools(): AgentMcpTool[] {
    return this.#registry.list().map((capability) => ({
      description: capability.description,
      inputSchema: capability.inputSchema,
      name: capability.id,
    }));
  }

  callTool(name: string, input: unknown): Promise<CapabilityInvocationResult> {
    return this.#registry.invoke(name, input, { interface: "mcp" });
  }
}
