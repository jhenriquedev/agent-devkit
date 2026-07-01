import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ErrorCodes } from "../infra/bases/errors";
import { createCapabilityToolRuntime } from "./capability_tool_runtime";

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

describe("CapabilityToolRuntime", () => {
  it("lists tools with schemas, risk and approval metadata", () => {
    const tools = runtime().listTools();

    expect(tools.map((tool) => tool.id)).toEqual([
      "context.projects",
      "context.sessions",
      "environment.dependencies",
      "logs.analysis",
      "project.doctor",
      "project.init",
      "project.reset",
      "secrets.vault",
      "self.update",
      "user.personalization",
      "user.preferences",
    ]);
    expect(tools).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "project.doctor",
          approval: { required: false, reason: "Capability is read-only." },
          inputSchema: expect.objectContaining({ type: "object" }),
          risk: "read-only",
        }),
      ]),
    );
  });

  it("rejects unknown tools with a structured failed result", async () => {
    const result = await runtime().execute({
      capabilityId: "missing.tool",
      input: {},
      interface: "agent",
    });

    expect(result).toMatchObject({
      capabilityId: "missing.tool",
      error: { code: ErrorCodes.CapabilityNotFound },
      status: "failed",
    });
  });

  it("rejects invalid input before executing the tool", async () => {
    const result = await runtime().execute({
      approved: true,
      capabilityId: "project.init",
      input: { dryRun: true },
      interface: "agent",
    });

    expect(result).toMatchObject({
      capabilityId: "project.init",
      error: { code: ErrorCodes.InvalidInput },
      status: "failed",
    });
  });

  it("requires approval for risky tools", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-runtime-reset-"));
    const projectRoot = join(root, "project");
    const homeDirectory = join(root, "home");

    try {
      await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });
      await mkdir(homeDirectory, { recursive: true });

      const result = await runtime().execute({
        capabilityId: "project.reset",
        input: {
          confirmed: true,
          dryRun: false,
          homeDirectory,
          projectRoot,
          scope: "project",
        },
        interface: "agent",
      });

      expect(result).toMatchObject({
        capabilityId: "project.reset",
        error: { code: ErrorCodes.ApprovalRequired },
        status: "approval_required",
      });
      expect(existsSync(join(projectRoot, ".agent-devkit"))).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("executes read-only tools and returns a standard runtime envelope", async () => {
    const result = await runtime().execute({
      capabilityId: "project.doctor",
      input: {},
      interface: "agent",
    });

    expect(result).toMatchObject({
      capabilityId: "project.doctor",
      effects: [{ operation: "read", scope: "none" }],
      output: {
        status: expect.any(String),
        version: "0.4.0",
      },
      risk: "read-only",
      status: "succeeded",
    });
  });
});
