import { createContextSurface } from "./context.surface";

describe("context surface", () => {
  it("loads context surface files and derives capabilities from configs", async () => {
    const surface = createContextSurface();
    const [capabilities, knowledge, loop, prompt, skill] = await Promise.all([
      surface.capabilities(),
      surface.knowledge(),
      surface.loop(),
      surface.prompt(),
      surface.skill(),
    ]);

    expect(capabilities.isOk()).toBe(true);
    expect(capabilities.unwrap().map((capability) => capability.id)).toEqual([
      "context.projects",
      "context.sessions",
    ]);
    expect(knowledge.isOk()).toBe(true);
    expect(loop.isOk()).toBe(true);
    expect(prompt.isOk()).toBe(true);
    expect(skill.isOk()).toBe(true);
  });
});
