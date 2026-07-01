import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

function parseToolText(result: Awaited<ReturnType<Client["callTool"]>>) {
  const [content] = result.content as { text?: string; type: string }[];

  if (content?.type !== "text") {
    throw new Error("Expected text tool result.");
  }

  return JSON.parse(content.text ?? "");
}

describe("agent mcp", () => {
  it("starts a real stdio MCP server", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-mcp-cli-"));
    const transport = new StdioClientTransport({
      args: [mainEntrypoint, "mcp", "stdio"],
      command: tsxBin,
      env: { ...process.env, HOME: home },
      stderr: "pipe",
    });
    const client = new Client({ name: "agent-devkit-stdio-test", version: "0.0.0" });

    try {
      await client.connect(transport);
      const tools = await client.listTools();
      const doctor = await client.callTool({ name: "project.doctor", arguments: {} });
      const payload = parseToolText(doctor);

      expect(tools.tools.map((tool) => tool.name)).toContain("project.doctor");
      expect(payload).toMatchObject({
        capabilityId: "project.doctor",
        status: "succeeded",
      });
    } finally {
      await client.close();
      await rm(home, { force: true, recursive: true });
    }
  });
});
