import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ErrorCodes } from "../../infra/bases/errors";
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

  it("rejects MCP tool calls that require approval by default", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-mcp-reset-"));
    const projectRoot = join(root, "project");
    const homeDirectory = join(root, "home");

    try {
      await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });
      await mkdir(homeDirectory, { recursive: true });

      const result = await adapter().callTool("project.reset", {
        dryRun: false,
        homeDirectory,
        projectRoot,
        scope: "project",
      });

      expect(result).toMatchObject({
        capabilityId: "project.reset",
        error: {
          code: ErrorCodes.ApprovalRequired,
        },
        ok: false,
      });
      expect(existsSync(join(projectRoot, ".agent-devkit"))).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("passes MCP approval context to the registry", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-mcp-approved-reset-"));
    const projectRoot = join(root, "project");
    const homeDirectory = join(root, "home");

    try {
      await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });
      await mkdir(homeDirectory, { recursive: true });

      const result = await adapter().callTool(
        "project.reset",
        {
          dryRun: false,
          homeDirectory,
          projectRoot,
          scope: "project",
        },
        { approved: true },
      );

      expect(result).toMatchObject({
        capabilityId: "project.reset",
        data: { removed: true },
        ok: true,
      });
      expect(existsSync(join(projectRoot, ".agent-devkit"))).toBe(false);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
