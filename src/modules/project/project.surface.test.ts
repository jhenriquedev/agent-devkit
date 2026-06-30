import { createProjectSurface } from "./project.surface";

describe("project module surface", () => {
  it("loads validated project module surface files", async () => {
    const surface = createProjectSurface();

    const skill = await surface.skill();
    const knowledge = await surface.knowledge();
    const prompt = await surface.prompt({ capabilityId: "project.doctor" });
    const loop = await surface.loop();
    const capabilities = await surface.capabilities();

    expect(skill.isOk()).toBe(true);
    expect(knowledge.isOk()).toBe(true);
    expect(prompt.isOk()).toBe(true);
    expect(loop.isOk()).toBe(true);
    expect(capabilities.isOk()).toBe(true);

    expect(skill.unwrap()).toMatchObject({
      moduleId: "project",
      purpose: expect.any(String),
    });
    expect(knowledge.unwrap()).toMatchObject({
      moduleId: "project",
      summary: expect.any(String),
    });
    expect(prompt.unwrap()).toMatchObject({
      moduleId: "project",
      templates: expect.any(Array),
    });
    expect(loop.unwrap()).toMatchObject({
      moduleId: "project",
      mode: expect.any(String),
    });
    expect(capabilities.unwrap()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: "project.doctor" }),
        expect.objectContaining({ id: "project.init" }),
        expect.objectContaining({ id: "project.reset" }),
      ]),
    );
  });
});
