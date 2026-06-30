import { execFile } from "node:child_process";
import { mkdtemp, readFile, realpath, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

describe("agent init", () => {
  it("prints a dry-run plan without creating project state", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-init-cli-"));

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "init", "--dry-run"], {
        cwd: projectRoot,
      });

      expect(stdout).toContain("Agent DevKit Init");
      expect(stdout).toContain("[planned] project state");
      expect(stdout).toContain(".agent-devkit/config.json");
      await expect(
        readFile(join(projectRoot, ".agent-devkit", "config.json"), "utf8"),
      ).rejects.toThrow();
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });

  it("prints structured JSON when initializing a project", async () => {
    const projectRoot = await mkdtemp(join(tmpdir(), "agent-devkit-init-cli-"));

    try {
      const resolvedProjectRoot = await realpath(projectRoot);
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "init", "--json"], {
        cwd: projectRoot,
      });
      const result = JSON.parse(stdout);

      expect(result.status).toBe("initialized");
      expect(result.project.root).toBe(resolvedProjectRoot);
      expect(result.created).toEqual([
        ".agent-devkit/config.json",
        ".agent-devkit/agent-devkit.lock",
      ]);
    } finally {
      await rm(projectRoot, { force: true, recursive: true });
    }
  });
});
