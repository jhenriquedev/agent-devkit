import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, realpath, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

describe("agent doctor", () => {
  it("prints a human-readable doctor report", async () => {
    const cwd = await mkdtemp(join(tmpdir(), "agent-devkit-cli-"));

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "doctor"], {
        cwd,
        env: { ...process.env, HOME: cwd },
      });

      expect(stdout).toContain("Agent DevKit Doctor");
      expect(stdout).toContain("Versao: 0.4.0");
      expect(stdout).toContain("Estado global:");
      expect(stdout).toContain("Estado do projeto:");
    } finally {
      await rm(cwd, { force: true, recursive: true });
    }
  });

  it("prints doctor JSON without creating global state", async () => {
    const homeDirectory = await mkdtemp(join(tmpdir(), "agent-devkit-home-"));
    const projectDirectory = await mkdtemp(join(tmpdir(), "agent-devkit-project-"));

    try {
      const resolvedProjectDirectory = await realpath(projectDirectory);
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "doctor", "--json"], {
        cwd: projectDirectory,
        env: { ...process.env, HOME: homeDirectory },
      });

      const report = JSON.parse(stdout);

      expect(report.status).toBe("warning");
      expect(report.version).toBe("0.4.0");
      expect(report.runtime.globalState).toEqual({
        path: join(homeDirectory, ".agent-devkit"),
        exists: false,
      });
      expect(report.runtime.projectState).toEqual({
        path: join(resolvedProjectDirectory, ".agent-devkit"),
        exists: false,
      });
      expect(existsSync(join(homeDirectory, ".agent-devkit"))).toBe(false);
    } finally {
      await rm(homeDirectory, { force: true, recursive: true });
      await rm(projectDirectory, { force: true, recursive: true });
    }
  });
});
