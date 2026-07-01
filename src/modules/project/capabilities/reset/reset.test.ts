import { mkdir, mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ResetRepository } from "./reset.repository";
import { ResetService } from "./reset.service";

describe("project.reset", () => {
  it("plans local project state removal without deleting files in dry-run mode", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-reset-"));
    await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });

    try {
      const result = await new ResetService({
        repository: new ResetRepository(),
      }).execute({ dryRun: true, homeDirectory: "/home/tester", projectRoot, scope: "project" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        scope: "project",
        status: "planned",
        removed: false,
        path: join(projectRoot, ".agent-devkit"),
      });
      await expect(readdir(join(projectRoot, ".agent-devkit"))).resolves.toEqual([]);
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });

  it("removes local project state when confirmed", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-reset-"));
    await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });

    try {
      const result = await new ResetService({
        repository: new ResetRepository(),
      }).execute({
        confirmed: true,
        dryRun: false,
        homeDirectory: "/home/tester",
        projectRoot,
        scope: "project",
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap().status).toBe("reset");
      expect(result.unwrap().removed).toBe(true);
      await expect(readdir(join(projectRoot, ".agent-devkit"))).rejects.toThrow();
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });
});
