import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { LocalAgentDataStore } from "../../../../infra/data";
import { ContextProjectsRepository } from "../../../context/capabilities/projects/projects.repository";
import { ContextProjectsService } from "../../../context/capabilities/projects/projects.service";
import { ContextSessionsRepository } from "../../../context/capabilities/sessions/sessions.repository";
import { PersonalizationRepository } from "../../../user/capabilities/personalization/personalization.repository";
import { ConversationChatRepository } from "./chat.repository";
import { ConversationChatService, MockBrainProvider } from "./chat.service";

function service(root: string): {
  chat: ConversationChatService;
  projects: ContextProjectsService;
} {
  const dataStore = new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") });
  const clock = () => new Date("2026-07-01T20:30:00.000Z");

  return {
    chat: new ConversationChatService({
      brainProvider: new MockBrainProvider(),
      repository: new ConversationChatRepository({
        clock,
        personalizationRepository: new PersonalizationRepository({ dataStore }),
        projectsRepository: new ContextProjectsRepository({ clock, dataStore }),
        sessionsRepository: new ContextSessionsRepository({
          clock,
          dataStore,
          idFactory: () => "ses_chat_test",
          messageIdFactory: () => "msg_chat_test",
        }),
      }),
    }),
    projects: new ContextProjectsService({
      repository: new ContextProjectsRepository({ clock, dataStore }),
    }),
  };
}

describe("conversation.chat", () => {
  it("creates a session, saves the conversation and builds a canonical prompt", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-conversation-chat-"));
    const { chat, projects } = service(root);

    try {
      await projects.execute({
        action: "create",
        description: "Agent DevKit rewrite",
        name: "Agent DevKit",
        path: "/repo/agent-devkit",
        tags: ["typescript"],
      });

      const result = await chat.execute({
        action: "send",
        message: "Analise a arquitetura atual do projeto.",
        projectId: "proj_agent_devkit",
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "send",
        projectId: "proj_agent_devkit",
        reply: expect.stringContaining("Analise a arquitetura atual do projeto."),
        sessionId: "ses_chat_test",
      });
      expect(result.unwrap().messages).toEqual([
        expect.objectContaining({
          content: "Analise a arquitetura atual do projeto.",
          role: "user",
        }),
        expect.objectContaining({
          role: "assistant",
        }),
      ]);
      expect(result.unwrap().prompt).toMatchObject({
        agent: {
          characterId: expect.any(String),
          name: expect.any(String),
        },
        context: {
          knowledge: expect.arrayContaining([
            expect.objectContaining({
              id: "agent-devkit.identity",
            }),
            expect.objectContaining({
              id: "agent-devkit.self-description-rule",
            }),
            expect.objectContaining({
              id: "agent-devkit.project-scope-rule",
            }),
            expect.objectContaining({
              id: "agent-devkit.chat-mode-limits",
            }),
          ]),
          project: {
            id: "proj_agent_devkit",
            name: "Agent DevKit",
          },
          session: {
            id: "ses_chat_test",
          },
        },
        policies: {
          allowToolCalls: false,
        },
        task: {
          userMessage: "Analise a arquitetura atual do projeto.",
        },
      });
      expect(
        result
          .unwrap()
          .prompt.context.knowledge.map((knowledge) => knowledge.content)
          .join("\n"),
      ).toContain("Do not answer as a generic human");
      expect(result.unwrap().brain).toMatchObject({
        finishReason: "stop",
        provider: "mock",
        text: result.unwrap().reply,
      });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("answers personal capability questions from the character persona", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-conversation-chat-"));
    const { chat } = service(root);

    try {
      const result = await chat.execute({
        action: "send",
        message: "o que você pode fazer?",
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        brain: {
          model: "self-description",
          provider: "system",
        },
        sessionId: "ses_chat_test",
      });
      expect(result.unwrap().reply).toContain("Eu posso conversar com voce");
      expect(result.unwrap().reply).toContain("meu tom");
      expect(result.unwrap().reply).not.toContain("Agent DevKit");
      expect(result.unwrap().reply).not.toContain("MCP");
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("resumes an existing session and can omit history from the prompt", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-conversation-chat-"));
    const { chat } = service(root);

    try {
      const first = await chat.execute({
        action: "send",
        message: "Primeira mensagem.",
      });
      const second = await chat.execute({
        action: "send",
        includeHistory: false,
        message: "Segunda mensagem.",
        sessionId: "ses_chat_test",
      });

      expect(first.isOk()).toBe(true);
      expect(second.isOk()).toBe(true);
      expect(second.unwrap()).toMatchObject({
        sessionId: "ses_chat_test",
      });
      expect(second.unwrap().prompt.messages).toEqual([
        expect.objectContaining({
          content: "Segunda mensagem.",
          role: "user",
        }),
      ]);
      expect(second.unwrap().messages).toHaveLength(4);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects attaching a standalone session to a project through chat input", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-conversation-chat-"));
    const { chat, projects } = service(root);

    try {
      await projects.execute({ action: "create", name: "Agent DevKit" });
      const first = await chat.execute({
        action: "send",
        message: "Sessao standalone.",
      });
      const second = await chat.execute({
        action: "send",
        message: "Tente usar contexto de projeto.",
        projectId: "proj_agent_devkit",
        sessionId: "ses_chat_test",
      });

      expect(first.isOk()).toBe(true);
      expect(second.isErr()).toBe(true);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
