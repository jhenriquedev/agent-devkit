import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ErrorCodes } from "../infra/bases/errors";
import { createAgentCapabilityRegistry } from "./capability_registry";

function registry() {
  return createAgentCapabilityRegistry({
    appVersion: "0.4.0",
    currentVersion: "0.4.0",
    packageName: "agent-devkit",
  });
}

describe("agent capability registry", () => {
  it("lists invokable capabilities with runtime schemas and risk metadata", () => {
    const result = registry();

    expect(result.isOk()).toBe(true);

    const capabilities = result.unwrap().list();

    expect(capabilities.map((capability) => capability.id)).toEqual([
      "context.projects",
      "context.sessions",
      "conversation.chat",
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
    expect(capabilities).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "conversation.chat",
          approval: {
            reason: "Capability writes global state.",
            required: true,
          },
          inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          outputSchema: expect.objectContaining({ type: "object" }),
          risk: "writes-global-state",
        }),
        expect.objectContaining({
          id: "context.projects",
          approval: {
            reason: "Capability writes global state.",
            required: true,
          },
          inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          outputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          risk: "writes-global-state",
        }),
        expect.objectContaining({
          id: "context.sessions",
          approval: {
            reason: "Capability writes global state.",
            required: true,
          },
          inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          outputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          risk: "writes-global-state",
        }),
        expect.objectContaining({
          id: "environment.dependencies",
          approval: {
            reason: "Capability is read-only.",
            required: false,
          },
          inputSchema: expect.objectContaining({ type: "object" }),
          risk: "read-only",
        }),
        expect.objectContaining({
          id: "project.init",
          approval: {
            reason: "Capability writes project state.",
            required: true,
          },
          inputSchema: expect.objectContaining({ type: "object" }),
          kind: "deterministic",
          outputSchema: expect.objectContaining({ type: "object" }),
          risk: "writes-project-state",
        }),
        expect.objectContaining({
          id: "secrets.vault",
          approval: {
            reason: "Capability writes global state.",
            required: true,
          },
          inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          outputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          risk: "writes-global-state",
        }),
        expect.objectContaining({
          id: "project.doctor",
          approval: {
            reason: "Capability is read-only.",
            required: false,
          },
        }),
        expect.objectContaining({
          id: "project.reset",
          approval: {
            reason: "Capability can remove state and requires explicit approval.",
            required: true,
          },
        }),
        expect.objectContaining({
          id: "user.personalization",
          approval: {
            reason: "Capability writes global state.",
            required: true,
          },
          inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
          risk: "writes-global-state",
        }),
      ]),
    );
  });

  it("rejects invalid input before invoking a capability", async () => {
    const result = registry();
    const invocation = await result
      .unwrap()
      .invoke("project.init", { dryRun: true }, { approved: true, interface: "agent" });

    expect(invocation).toMatchObject({
      ok: false,
      capabilityId: "project.init",
      error: {
        code: ErrorCodes.InvalidInput,
        recoverable: true,
      },
    });
  });

  it("rejects dangerous capabilities without explicit approval before side effects", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-registry-reset-"));
    const projectRoot = join(root, "project");
    const homeDirectory = join(root, "home");

    try {
      await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });
      await mkdir(homeDirectory, { recursive: true });

      const result = registry();
      const invocation = await result.unwrap().invoke(
        "project.reset",
        {
          confirmed: true,
          dryRun: false,
          homeDirectory,
          projectRoot,
          scope: "project",
        },
        { interface: "agent" },
      );

      expect(invocation).toMatchObject({
        ok: false,
        capabilityId: "project.reset",
        error: {
          code: ErrorCodes.ApprovalRequired,
          recoverable: true,
        },
      });
      expect(existsSync(join(projectRoot, ".agent-devkit"))).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("invokes dangerous capabilities after explicit approval", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-registry-approved-reset-"));
    const projectRoot = join(root, "project");
    const homeDirectory = join(root, "home");

    try {
      await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });
      await mkdir(homeDirectory, { recursive: true });

      const result = registry();
      const invocation = await result.unwrap().invoke(
        "project.reset",
        {
          confirmed: true,
          dryRun: false,
          homeDirectory,
          projectRoot,
          scope: "project",
        },
        { approved: true, interface: "agent" },
      );

      expect(invocation).toMatchObject({
        ok: true,
        capabilityId: "project.reset",
        data: {
          removed: true,
          status: "reset",
        },
      });
      expect(existsSync(join(projectRoot, ".agent-devkit"))).toBe(false);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects global-state capabilities without explicit approval", async () => {
    const result = registry();
    const invocation = await result
      .unwrap()
      .invoke("secrets.vault", { action: "list" }, { interface: "agent" });

    expect(invocation).toMatchObject({
      ok: false,
      capabilityId: "secrets.vault",
      error: {
        code: ErrorCodes.ApprovalRequired,
      },
    });
  });

  it("requires approval for context hard deletes through the registry", async () => {
    const result = registry();
    const invocation = await result
      .unwrap()
      .invoke(
        "context.sessions",
        { action: "delete", hard: true, sessionId: "ses_missing" },
        { interface: "agent" },
      );

    expect(invocation).toMatchObject({
      ok: false,
      capabilityId: "context.sessions",
      error: { code: ErrorCodes.ApprovalRequired },
    });
  });

  it("allows context read actions without approval through the registry", async () => {
    const result = registry();
    const projects = await result
      .unwrap()
      .invoke("context.projects", { action: "list" }, { interface: "agent" });
    const sessions = await result
      .unwrap()
      .invoke("context.sessions", { action: "search", query: "memory" }, { interface: "agent" });

    expect(projects).toMatchObject({
      ok: true,
      capabilityId: "context.projects",
      effects: [{ operation: "read", scope: "none" }],
    });
    expect(sessions).toMatchObject({
      ok: true,
      capabilityId: "context.sessions",
      effects: [{ operation: "read", scope: "none" }],
    });
  });

  it("allows conversation chat without approval while tool calls are disabled", async () => {
    const result = registry();
    const invocation = await result.unwrap().invoke(
      "conversation.chat",
      {
        action: "send",
        message: "Planeje a proxima entrega.",
      },
      { interface: "agent" },
    );

    expect(invocation).toMatchObject({
      ok: true,
      capabilityId: "conversation.chat",
      effects: [{ operation: "write", scope: "global" }],
    });
  });

  it("invokes a capability by id and returns a standard envelope", async () => {
    const result = registry();
    const invocation = await result.unwrap().invoke("project.doctor", {}, { interface: "agent" });

    expect(invocation).toMatchObject({
      ok: true,
      capabilityId: "project.doctor",
      data: {
        status: expect.any(String),
        version: "0.4.0",
      },
      effects: [
        {
          operation: "read",
          scope: "none",
        },
      ],
    });

    if (invocation.ok) {
      expect(invocation.audit.durationMs).toBeGreaterThanOrEqual(0);
      expect(invocation.audit.startedAt).toEqual(expect.any(String));
      expect(invocation.audit.endedAt).toEqual(expect.any(String));
    }
  });
});
