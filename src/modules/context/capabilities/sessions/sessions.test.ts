import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { LocalAgentDataStore } from "../../../../infra/data";
import { ContextProjectsRepository } from "../projects/projects.repository";
import { ContextProjectsService } from "../projects/projects.service";
import { ContextSessionsRepository } from "./sessions.repository";
import { ContextSessionsService } from "./sessions.service";

function repositories(root: string) {
  const dataStore = new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") });
  const clock = () => new Date("2026-07-01T20:10:00.000Z");

  return {
    projects: new ContextProjectsRepository({ clock, dataStore }),
    sessions: new ContextSessionsRepository({
      clock,
      dataStore,
      idFactory: () => "ses_test_session",
      messageIdFactory: () => "msg_test",
    }),
  };
}

describe("context.sessions", () => {
  it("creates standalone sessions, appends messages, searches, resumes and soft deletes", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-sessions-"));
    const repos = repositories(root);
    const sessions = new ContextSessionsService({ repository: repos.sessions });

    try {
      const created = await sessions.execute({
        action: "create",
        origin: "cli",
        tags: ["memory"],
      });
      const appended = await sessions.execute({
        action: "append-message",
        content: "Quero criar um sistema de sessoes para o agente ter memoria.",
        role: "user",
        sessionId: "ses_test_session",
      });
      const shown = await sessions.execute({
        action: "show",
        includeMessages: true,
        sessionId: "ses_test_session",
      });
      const searched = await sessions.execute({ action: "search", query: "memoria" });
      const resumed = await sessions.execute({ action: "resume", sessionId: "ses_test_session" });
      const deleted = await sessions.execute({ action: "delete", sessionId: "ses_test_session" });
      const listed = await sessions.execute({ action: "list" });
      const all = await sessions.execute({ action: "list", status: "all" });

      expect(created.unwrap()).toMatchObject({
        action: "create",
        session: {
          id: "ses_test_session",
          origin: "cli",
          status: "active",
          title: "Untitled session",
        },
      });
      expect(appended.unwrap()).toMatchObject({
        action: "append-message",
        index: {
          messageCount: 1,
          title: "Quero criar um sistema de sessoes para o agente ter memoria.",
        },
        message: {
          content: "Quero criar um sistema de sessoes para o agente ter memoria.",
          id: "msg_test",
        },
      });
      expect(shown.unwrap()).toMatchObject({
        action: "show",
        messages: [expect.objectContaining({ id: "msg_test" })],
        session: { title: "Quero criar um sistema de sessoes para o agente ter memoria." },
      });
      expect(searched.unwrap()).toMatchObject({
        action: "search",
        results: [expect.objectContaining({ sessionId: "ses_test_session" })],
      });
      expect(resumed.unwrap()).toMatchObject({
        action: "resume",
        messages: [expect.objectContaining({ id: "msg_test" })],
        session: { status: "active" },
      });
      expect(deleted.unwrap()).toMatchObject({
        action: "delete",
        hard: false,
        sessionId: "ses_test_session",
      });
      expect(listed.unwrap()).toMatchObject({ sessions: [] });
      expect(all.unwrap()).toMatchObject({
        sessions: [expect.objectContaining({ status: "deleted" })],
      });

      const messages = await readFile(
        join(
          root,
          ".agent-devkit",
          "data",
          "context",
          "sessions",
          "ses_test_session",
          "messages.jsonl",
        ),
        "utf8",
      );
      expect(messages.trim().split("\n")).toHaveLength(1);
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("stores project sessions inside the project tree", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-sessions-"));
    const repos = repositories(root);
    const projects = new ContextProjectsService({ repository: repos.projects });
    const sessions = new ContextSessionsService({ repository: repos.sessions });

    try {
      await projects.execute({ action: "create", name: "Agent DevKit" });
      const created = await sessions.execute({
        action: "create",
        origin: "mcp",
        projectId: "proj_agent_devkit",
        title: "Planejamento do contexto",
      });

      expect(created.unwrap()).toMatchObject({
        session: { id: "ses_test_session", projectId: "proj_agent_devkit" },
      });
      await expect(
        readFile(
          join(
            root,
            ".agent-devkit",
            "data",
            "context",
            "projects",
            "proj_agent_devkit",
            "sessions",
            "ses_test_session",
            "session.json",
          ),
          "utf8",
        ),
      ).resolves.toContain("Planejamento do contexto");
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects invalid service input before writing session state", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-sessions-"));
    const repos = repositories(root);
    const sessions = new ContextSessionsService({ repository: repos.sessions });

    try {
      const created = await sessions.execute({
        action: "create",
        origin: "invalid",
      } as never);

      expect(created.isErr()).toBe(true);
      await expect(
        readFile(
          join(root, ".agent-devkit", "data", "context", "sessions", "ses_test_session"),
          "utf8",
        ),
      ).rejects.toThrow();
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects invalid messages before appending JSONL records", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-sessions-"));
    const repos = repositories(root);
    const sessions = new ContextSessionsService({ repository: repos.sessions });

    try {
      await sessions.execute({ action: "create", origin: "cli" });
      const appended = await sessions.execute({
        action: "append-message",
        content: "Mensagem invalida.",
        role: "invalid",
        sessionId: "ses_test_session",
      } as never);

      expect(appended.isErr()).toBe(true);
      await expect(
        readFile(
          join(
            root,
            ".agent-devkit",
            "data",
            "context",
            "sessions",
            "ses_test_session",
            "messages.jsonl",
          ),
          "utf8",
        ),
      ).rejects.toThrow();
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("rejects sessions for missing projects without creating ghost project folders", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-sessions-"));
    const repos = repositories(root);
    const projects = new ContextProjectsService({ repository: repos.projects });
    const sessions = new ContextSessionsService({ repository: repos.sessions });

    try {
      const created = await sessions.execute({
        action: "create",
        origin: "cli",
        projectId: "proj_missing",
      });
      const listed = await projects.execute({ action: "list", status: "all" });

      expect(created.isErr()).toBe(true);
      expect(listed.isOk()).toBe(true);
      expect(listed.unwrap()).toEqual({ action: "list", projects: [] });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
