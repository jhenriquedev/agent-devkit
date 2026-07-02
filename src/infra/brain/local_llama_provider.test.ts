import { AgentPromptSchema } from "../bases/prompt";
import { systemPromptFrom } from "./local_llama_provider";

describe("local llama provider prompt", () => {
  it("anchors local models to Agent DevKit identity, knowledge and tool policy", () => {
    const prompt = AgentPromptSchema.parse({
      agent: {
        behavior: "balanced",
        characterId: "kit",
        detailLevel: "concise",
        name: "kit",
        tone: "direct",
        traits: ["pragmatic"],
      },
      context: {
        knowledge: [
          {
            content: "When the user asks what you can do, answer from your configured persona.",
            id: "agent-devkit.self-description-rule",
          },
          {
            content:
              "This conversation mode can answer and keep session memory; direct tool execution is disabled.",
            id: "agent-devkit.chat-mode-limits",
          },
        ],
        session: {
          id: "ses_test",
          messageCount: 1,
          title: "o que voce pode fazer?",
        },
      },
      locale: "pt-BR",
      messages: [
        {
          content: "o que voce pode fazer?",
          role: "user",
        },
      ],
      output: { format: "text", language: "pt-BR" },
      policies: {
        allowToolCalls: false,
        approvalRequired: false,
        maxToolCalls: 0,
      },
      schema: "agent-devkit.prompt/v1",
      task: {
        userMessage: "o que voce pode fazer?",
      },
      tools: [],
    });

    const systemPrompt = systemPromptFrom(prompt);

    expect(systemPrompt).toContain("You are kit");
    expect(systemPrompt).toContain("Agent DevKit");
    expect(systemPrompt).toContain("Do not answer as the user");
    expect(systemPrompt).toContain("Do not list generic human activities");
    expect(systemPrompt).toContain("answer from your configured persona");
    expect(systemPrompt).toContain("Do not describe Agent DevKit internals unless");
    expect(systemPrompt).toContain("Tool calls allowed: no");
    expect(systemPrompt).toContain("direct tool execution is unavailable");
    expect(systemPrompt).toContain("Reply in pt-BR");
  });
});
