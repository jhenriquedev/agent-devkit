import { createEnvironmentSurface } from "./environment.surface";

describe("environment module surface", () => {
  it("loads validated environment module surface files", async () => {
    const surface = createEnvironmentSurface();
    const skill = await surface.skill();
    const capabilities = await surface.capabilities();

    expect(skill.isOk()).toBe(true);
    expect(capabilities.isOk()).toBe(true);
    expect(skill.unwrap()).toMatchObject({ moduleId: "environment" });
    expect(capabilities.unwrap()).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "environment.dependencies" })]),
    );
  });
});
