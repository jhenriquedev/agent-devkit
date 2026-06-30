import { execFile } from "node:child_process";
import { mkdir, mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

describe("agent reset", () => {
  it("prints a dry-run plan without removing local project state", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-reset-cli-"));
    await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "reset", "--dry-run"], {
        cwd: projectRoot,
      });

      expect(stdout).toContain("Agent DevKit Reset");
      expect(stdout).toContain("[planned] project state");
      await expect(readdir(join(projectRoot, ".agent-devkit"))).resolves.toEqual([]);
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });

  it("removes local project state only when confirmed", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-reset-cli-"));
    await mkdir(join(projectRoot, ".agent-devkit"), { recursive: true });

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "reset", "--yes", "--json"], {
        cwd: projectRoot,
      });
      const result = JSON.parse(stdout);

      expect(result.status).toBe("reset");
      expect(result.scope).toBe("project");
      await expect(readdir(join(projectRoot, ".agent-devkit"))).rejects.toThrow();
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });
});
