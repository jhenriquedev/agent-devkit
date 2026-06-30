import { createSelfSurface } from "./self.surface";

describe("self module surface", () => {
  it("loads validated self module surface files", async () => {
    const surface = createSelfSurface();

    const skill = await surface.skill();
    const capabilities = await surface.capabilities();

    expect(skill.isOk()).toBe(true);
    expect(capabilities.isOk()).toBe(true);

    expect(skill.unwrap()).toMatchObject({
      moduleId: "self",
      purpose: expect.any(String),
    });
    expect(capabilities.unwrap()).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "self.update" })]),
    );
  });
});
