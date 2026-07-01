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
      "logs.analysis",
      "project.doctor",
      "project.init",
      "project.reset",
      "secrets.vault",
      "self.update",
      "user.preferences",
    ]);
    expect(capabilities).toEqual(
      expect.arrayContaining([
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
      ]),
    );
  });

  it("rejects invalid input before invoking a capability", async () => {
    const result = registry();
    const invocation = await result
      .unwrap()
      .invoke("project.init", { dryRun: true }, { interface: "agent" });

    expect(invocation).toMatchObject({
      ok: false,
      capabilityId: "project.init",
      error: {
        code: ErrorCodes.InvalidInput,
        recoverable: true,
      },
    });
  });

  it("invokes a capability by id and returns a standard envelope", async () => {
    const result = registry();
    const invocation = await result.unwrap().invoke("project.doctor", {}, { interface: "agent" });

    expect(invocation).toMatchObject({
      ok: true,
      capabilityId: "project.doctor",
      data: {
        status: "ok",
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
