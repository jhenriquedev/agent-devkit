import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { InitializeProject } from "../src/domain/usecases/InitializeProject";
import { FileProjectStateRepository } from "../src/infra/repositories/FileProjectStateRepository";

describe("InitializeProject", () => {
  it("plans project state files without writing them in dry-run mode", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-init-"));

    try {
      const repository = new FileProjectStateRepository();
      const result = await new InitializeProject({
        appVersion: "0.4.0",
        projectRoot,
        repository,
      }).execute({ dryRun: true });

      expect(result.status).toBe("planned");
      expect(result.created).toEqual([]);
      expect(result.skipped).toEqual([]);
      expect(result.planned).toEqual([
        ".agent-devkit/config.json",
        ".agent-devkit/agent-devkit.lock",
      ]);
      await expect(
        readFile(join(projectRoot, ".agent-devkit", "config.json"), "utf8"),
      ).rejects.toThrow();
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });

  it("creates project state files and is idempotent", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-init-"));

    try {
      const repository = new FileProjectStateRepository();
      const initialize = new InitializeProject({
        appVersion: "0.4.0",
        projectRoot,
        repository,
      });

      const first = await initialize.execute({ dryRun: false });
      const second = await initialize.execute({ dryRun: false });

      expect(first.status).toBe("initialized");
      expect(first.created).toEqual([
        ".agent-devkit/config.json",
        ".agent-devkit/agent-devkit.lock",
      ]);
      expect(second.status).toBe("already-initialized");
      expect(second.created).toEqual([]);
      expect(second.skipped).toEqual([
        ".agent-devkit/config.json",
        ".agent-devkit/agent-devkit.lock",
      ]);

      const config = JSON.parse(
        await readFile(join(projectRoot, ".agent-devkit", "config.json"), "utf8"),
      );
      const lock = JSON.parse(
        await readFile(join(projectRoot, ".agent-devkit", "agent-devkit.lock"), "utf8"),
      );

      expect(config).toMatchObject({
        schema: "agent-devkit.project-config/v1",
        version: "0.4.0",
      });
      expect(lock).toMatchObject({
        schema: "agent-devkit.project-lock/v1",
        version: "0.4.0",
      });
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });
});
