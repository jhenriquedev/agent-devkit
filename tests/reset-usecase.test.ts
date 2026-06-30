import { mkdir, mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ResetState } from "../src/domain/usecases/ResetState";
import { FileStateResetRepository } from "../src/infra/repositories/FileStateResetRepository";

describe("ResetState", () => {
  it("plans local project state removal without deleting files in dry-run mode", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-reset-"));
    await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });

    try {
      const result = await new ResetState({
        homeDirectory: "/home/tester",
        projectRoot,
        repository: new FileStateResetRepository(),
      }).execute({ dryRun: true, scope: "project" });

      expect(result).toMatchObject({
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
      const result = await new ResetState({
        homeDirectory: "/home/tester",
        projectRoot,
        repository: new FileStateResetRepository(),
      }).execute({ dryRun: false, scope: "project" });

      expect(result.status).toBe("reset");
      expect(result.removed).toBe(true);
      await expect(readdir(join(projectRoot, ".agent-devkit"))).rejects.toThrow();
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });
});
