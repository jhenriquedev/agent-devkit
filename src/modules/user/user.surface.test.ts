import { createUserSurface } from "./user.surface";

describe("user module surface", () => {
  it("loads validated user module surface files", async () => {
    const surface = createUserSurface();
    const skill = await surface.skill();
    const capabilities = await surface.capabilities();

    expect(skill.isOk()).toBe(true);
    expect(capabilities.isOk()).toBe(true);
    expect(skill.unwrap()).toMatchObject({ moduleId: "user" });
    expect(capabilities.unwrap()).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "user.preferences" })]),
    );
  });
});
