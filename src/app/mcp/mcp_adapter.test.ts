import { createAgentCapabilityRegistry } from "../../modules/capability_registry";
import { AgentMcpAdapter } from "./mcp_adapter";

function adapter() {
  const registry = createAgentCapabilityRegistry({
    appVersion: "0.4.0",
    currentVersion: "0.4.0",
    packageName: "agent-devkit",
  });

  if (registry.isErr()) {
    throw new Error(registry.unwrapError());
  }

  return new AgentMcpAdapter({ registry: registry.unwrap() });
}

describe("AgentMcpAdapter", () => {
  it("lists MCP tools from invokable capabilities", () => {
    const tools = adapter().listTools();

    expect(tools).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          description: "Inspect the local Agent DevKit environment without changing state.",
          inputSchema: expect.objectContaining({ type: "object" }),
          name: "project.doctor",
        }),
      ]),
    );
  });

  it("calls MCP tools through the capability registry", async () => {
    const result = await adapter().callTool("project.doctor", {});

    expect(result).toMatchObject({
      capabilityId: "project.doctor",
      data: { status: "ok" },
      ok: true,
    });
  });
});
