import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { InitRepository } from "./init.repository";
import { InitService } from "./init.service";

describe("project.init", () => {
  it("plans project state files without writing them in dry-run mode", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-init-"));

    try {
      const repository = new InitRepository();
      const result = await new InitService({
        appVersion: "0.3.3",
        repository,
      }).execute({ dryRun: true, projectRoot });

      expect(result.isOk()).toBe(true);
      const payload = result.unwrap();
      expect(payload.status).toBe("planned");
      expect(payload.created).toEqual([]);
      expect(payload.skipped).toEqual([]);
      expect(payload.planned).toEqual([
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
      const repository = new InitRepository();
      const initialize = new InitService({
        appVersion: "0.3.3",
        repository,
      });

      const first = await initialize.execute({ dryRun: false, projectRoot });
      const second = await initialize.execute({ dryRun: false, projectRoot });

      expect(first.isOk()).toBe(true);
      expect(second.isOk()).toBe(true);
      const firstPayload = first.unwrap();
      const secondPayload = second.unwrap();

      expect(firstPayload.status).toBe("initialized");
      expect(firstPayload.created).toEqual([
        ".agent-devkit/config.json",
        ".agent-devkit/agent-devkit.lock",
      ]);
      expect(secondPayload.status).toBe("already-initialized");
      expect(secondPayload.created).toEqual([]);
      expect(secondPayload.skipped).toEqual([
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
        version: "0.3.3",
      });
      expect(lock).toMatchObject({
        schema: "agent-devkit.project-lock/v1",
        version: "0.3.3",
      });
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });
});
