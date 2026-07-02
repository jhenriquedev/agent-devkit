import { createLogsSurface } from "./logs.surface";

describe("logs module surface", () => {
  it("loads validated logs module surface files", async () => {
    const surface = createLogsSurface();
    const skill = await surface.skill();
    const capabilities = await surface.capabilities();

    expect(skill.isOk()).toBe(true);
    expect(capabilities.isOk()).toBe(true);
    expect(skill.unwrap()).toMatchObject({ moduleId: "logs" });
    expect(capabilities.unwrap()).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "logs.analysis" })]),
    );
  });
});
