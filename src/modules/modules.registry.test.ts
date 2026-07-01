import { agentModuleDefinitions } from "./modules.registry";

const moduleOptions = {
  appVersion: "0.4.0",
  currentVersion: "0.4.0",
  packageName: "agent-devkit",
};

describe("agent module definitions", () => {
  it("lists modules from one central manifest", () => {
    expect(agentModuleDefinitions.map((module) => module.id)).toEqual([
      "environment",
      "logs",
      "project",
      "secrets",
      "self",
      "user",
    ]);
  });

  it("binds capabilities through the central manifest", () => {
    const capabilityIds = agentModuleDefinitions.flatMap((definition) => {
      const binding = definition.bind(moduleOptions);

      expect(binding.isOk()).toBe(true);

      return definition
        .capabilities(binding.unwrap())
        .map((capability) => capability.capability.id);
    });

    expect(capabilityIds).toEqual([
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
  });

  it("derives surface capabilities from service configs to prevent drift", async () => {
    for (const definition of agentModuleDefinitions) {
      const binding = definition.bind(moduleOptions);
      const surface = definition.surface();
      const surfaceCapabilities = await surface.capabilities();

      expect(binding.isOk()).toBe(true);
      expect(surfaceCapabilities.isOk()).toBe(true);
      expect(surfaceCapabilities.unwrap()).toEqual(
        definition.capabilities(binding.unwrap()).map((capability) => ({
          id: capability.capability.id,
          kind: capability.capability.kind,
          risk: capability.capability.risk,
          summary: capability.capability.description,
          title: capability.capability.name,
        })),
      );
    }
  });
});
