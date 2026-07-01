import { createConversationSurface } from "./conversation.surface";

describe("conversation surface", () => {
  it("loads conversation surface files and derives capabilities from configs", async () => {
    const surface = createConversationSurface();
    const [capabilities, knowledge, loop, prompt, skill] = await Promise.all([
      surface.capabilities(),
      surface.knowledge(),
      surface.loop(),
      surface.prompt(),
      surface.skill(),
    ]);

    expect(capabilities.isOk()).toBe(true);
    expect(capabilities.unwrap().map((capability) => capability.id)).toEqual(["conversation.chat"]);
    expect(knowledge.isOk()).toBe(true);
    expect(loop.isOk()).toBe(true);
    expect(prompt.isOk()).toBe(true);
    expect(skill.isOk()).toBe(true);
  });
});
