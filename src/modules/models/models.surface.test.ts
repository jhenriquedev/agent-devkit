import { createModelsSurface } from "./models.surface";

describe("models module surface", () => {
  it("loads validated models module surface files", async () => {
    const surface = createModelsSurface();
    const skill = await surface.skill();
    const capabilities = await surface.capabilities();

    expect(skill.isOk()).toBe(true);
    expect(capabilities.isOk()).toBe(true);
    expect(skill.unwrap()).toMatchObject({ moduleId: "models" });
    expect(capabilities.unwrap()).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "models.registry" })]),
    );
  });
});
