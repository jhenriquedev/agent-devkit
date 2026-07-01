import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { LocalAgentDataStore } from "../../../../infra/data";
import { ContextProjectsRepository } from "./projects.repository";
import { ContextProjectsService } from "./projects.service";

function service(root: string): ContextProjectsService {
  return new ContextProjectsService({
    repository: new ContextProjectsRepository({
      clock: () => new Date("2026-07-01T20:00:00.000Z"),
      dataStore: new LocalAgentDataStore({ rootDirectory: join(root, ".agent-devkit", "data") }),
    }),
  });
}

describe("context.projects", () => {
  it("creates, lists, shows, updates, archives and soft deletes projects", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-projects-"));
    const projects = service(root);

    try {
      const created = await projects.execute({
        action: "create",
        description: "Rewrite v0.4.0",
        name: "Agent DevKit",
        path: "/repo/agent-devkit",
        tags: ["typescript", "cli"],
      });

      expect(created.isOk()).toBe(true);
      expect(created.unwrap()).toMatchObject({
        action: "create",
        project: {
          id: "proj_agent_devkit",
          name: "Agent DevKit",
          status: "active",
          tags: ["typescript", "cli"],
        },
      });

      const projectFile = await readFile(
        join(
          root,
          ".agent-devkit",
          "data",
          "context",
          "projects",
          "proj_agent_devkit",
          "project.json",
        ),
        "utf8",
      );
      const knowledgeBase = await readFile(
        join(
          root,
          ".agent-devkit",
          "data",
          "context",
          "projects",
          "proj_agent_devkit",
          "knowledge",
          "base.md",
        ),
        "utf8",
      );

      expect(projectFile).toContain("agent-devkit.context-project/v1");
      expect(knowledgeBase).toContain("Project Knowledge Base");

      const listed = await projects.execute({ action: "list", query: "typescript" });
      const shown = await projects.execute({ action: "show", projectId: "proj_agent_devkit" });
      const updated = await projects.execute({
        action: "update",
        name: "Agent DevKit Runtime",
        projectId: "proj_agent_devkit",
        tags: ["runtime"],
      });
      const archived = await projects.execute({
        action: "archive",
        projectId: "proj_agent_devkit",
      });
      const deleted = await projects.execute({ action: "delete", projectId: "proj_agent_devkit" });
      const active = await projects.execute({ action: "list" });
      const all = await projects.execute({ action: "list", status: "all" });

      expect(listed.unwrap()).toMatchObject({
        action: "list",
        projects: [expect.objectContaining({ id: "proj_agent_devkit" })],
      });
      expect(shown.unwrap()).toMatchObject({
        action: "show",
        project: { id: "proj_agent_devkit" },
      });
      expect(updated.unwrap()).toMatchObject({
        action: "update",
        project: { name: "Agent DevKit Runtime", tags: ["runtime"] },
      });
      expect(archived.unwrap()).toMatchObject({
        action: "archive",
        project: { status: "archived" },
      });
      expect(deleted.unwrap()).toMatchObject({
        action: "delete",
        hard: false,
        projectId: "proj_agent_devkit",
      });
      expect(active.unwrap()).toMatchObject({ projects: [] });
      expect(all.unwrap()).toMatchObject({
        projects: [expect.objectContaining({ status: "deleted" })],
      });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });

  it("hard deletes a project directory", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-context-projects-"));
    const projects = service(root);

    try {
      await projects.execute({ action: "create", name: "Disposable Project" });

      const deleted = await projects.execute({
        action: "delete",
        hard: true,
        projectId: "proj_disposable_project",
      });
      const all = await projects.execute({ action: "list", status: "all" });

      expect(deleted.unwrap()).toMatchObject({
        action: "delete",
        hard: true,
        projectId: "proj_disposable_project",
      });
      expect(all.unwrap()).toMatchObject({ projects: [] });
    } finally {
      await rm(root, { force: true, recursive: true });
    }
  });
});
