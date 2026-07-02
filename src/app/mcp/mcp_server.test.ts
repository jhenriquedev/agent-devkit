import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { ErrorCodes } from "../../infra/bases/errors";
import { createCapabilityToolRuntime } from "../../modules/capability_tool_runtime";
import { startMcpHttpServer } from "./mcp_http_transport";
import { createAgentMcpServer } from "./mcp_server";

function runtime() {
  const result = createCapabilityToolRuntime({
    appVersion: "0.4.0",
    currentVersion: "0.4.0",
    packageName: "agent-devkit",
  });

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  return result.unwrap();
}

function parseToolText(result: Awaited<ReturnType<Client["callTool"]>>) {
  const [content] = result.content as { text?: string; type: string }[];

  if (content?.type !== "text") {
    throw new Error("Expected text tool result.");
  }

  return JSON.parse(content.text ?? "");
}

describe("Agent MCP server", () => {
  it("lists and calls tools through MCP in-memory transport", async () => {
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    const activeRuntime = runtime();
    const server = createAgentMcpServer({
      packageName: "agent-devkit",
      runtime: activeRuntime,
      version: "0.4.0",
    });
    const client = new Client({ name: "agent-devkit-test", version: "0.0.0" });

    await server.connect(serverTransport);
    await client.connect(clientTransport);

    try {
      const tools = await client.listTools();
      const doctor = await client.callTool({ name: "project.doctor", arguments: {} });
      const doctorResult = parseToolText(doctor);
      const runtimeToolNames = activeRuntime.listTools().map((tool) => tool.id);

      expect(tools.tools.map((tool) => tool.name)).toEqual(["agent.task", ...runtimeToolNames]);
      expect(tools.tools).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            name: "context.projects",
            inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          }),
          expect.objectContaining({
            name: "context.sessions",
            inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          }),
          expect.objectContaining({
            name: "environment.dependencies",
            inputSchema: expect.objectContaining({ type: "object" }),
          }),
          expect.objectContaining({
            name: "project.doctor",
            inputSchema: expect.objectContaining({ type: "object" }),
          }),
          expect.objectContaining({
            name: "user.personalization",
            inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          }),
        ]),
      );
      expect(doctorResult).toMatchObject({
        capabilityId: "project.doctor",
        output: { version: "0.4.0" },
        status: "succeeded",
      });

      const environment = await client.callTool({
        name: "environment.dependencies",
        arguments: { action: "verify", dependency: "node" },
      });
      const environmentResult = parseToolText(environment);

      expect(environmentResult).toMatchObject({
        capabilityId: "environment.dependencies",
        output: { action: "verify", status: "ok" },
        status: "succeeded",
      });
    } finally {
      await client.close();
      await server.close();
    }
  });

  it("returns approval_required for risky tools unless MCP input approves them", async () => {
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    const server = createAgentMcpServer({
      packageName: "agent-devkit",
      runtime: runtime(),
      version: "0.4.0",
    });
    const client = new Client({ name: "agent-devkit-test", version: "0.0.0" });

    await server.connect(serverTransport);
    await client.connect(clientTransport);

    try {
      const result = await client.callTool({
        name: "project.reset",
        arguments: {
          confirmed: true,
          dryRun: true,
          homeDirectory: "/tmp/agent-devkit-home",
          projectRoot: "/tmp/agent-devkit-project",
          scope: "project",
        },
      });
      const payload = parseToolText(result);

      expect(payload).toMatchObject({
        capabilityId: "project.reset",
        error: { code: ErrorCodes.ApprovalRequired },
        status: "approval_required",
      });

      const approved = await client.callTool({
        name: "project.reset",
        arguments: {
          _agent: { approved: true },
          confirmed: true,
          dryRun: true,
          homeDirectory: "/tmp/agent-devkit-home",
          projectRoot: "/tmp/agent-devkit-project",
          scope: "project",
        },
      });
      const approvedPayload = parseToolText(approved);

      expect(approvedPayload).toMatchObject({
        capabilityId: "project.reset",
        output: { status: expect.any(String) },
        status: "succeeded",
      });
    } finally {
      await client.close();
      await server.close();
    }
  });

  it("serves MCP over local Streamable HTTP", async () => {
    const httpServer = await startMcpHttpServer({
      host: "127.0.0.1",
      packageName: "agent-devkit",
      port: 0,
      runtime: runtime(),
      version: "0.4.0",
    });
    const address = httpServer.address();
    const port = typeof address === "object" && address !== null ? address.port : 0;
    const client = new Client({ name: "agent-devkit-http-test", version: "0.0.0" });
    const transport = new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`));

    try {
      await client.connect(transport);
      const tools = await client.listTools();
      const doctor = await client.callTool({ name: "project.doctor", arguments: {} });
      const payload = parseToolText(doctor);

      expect(tools.tools.map((tool) => tool.name)).toContain("project.doctor");
      expect(payload.status).toBe("succeeded");
    } finally {
      await client.close();
      await new Promise<void>((resolve, reject) => {
        httpServer.close((error) => (error ? reject(error) : resolve()));
      });
    }
  });

  it("rejects forbidden HTTP origins before reading MCP requests", async () => {
    const httpServer = await startMcpHttpServer({
      allowedOrigins: ["http://allowed.local"],
      host: "127.0.0.1",
      packageName: "agent-devkit",
      port: 0,
      runtime: runtime(),
      version: "0.4.0",
    });
    const address = httpServer.address();
    const port = typeof address === "object" && address !== null ? address.port : 0;

    try {
      const response = await fetch(`http://127.0.0.1:${port}/mcp`, {
        body: "{}",
        headers: { origin: "http://evil.local" },
        method: "POST",
      });

      expect(response.status).toBe(403);
    } finally {
      await new Promise<void>((resolve, reject) => {
        httpServer.close((error) => (error ? reject(error) : resolve()));
      });
    }
  });
});
