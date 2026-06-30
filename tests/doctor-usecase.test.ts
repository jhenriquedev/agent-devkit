import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { RunDoctor } from "../src/domain/usecases/RunDoctor";

describe("RunDoctor", () => {
  it("reports environment state without creating Agent DevKit directories", async () => {
    const homeDirectory = await mkdtemp(join(tmpdir(), "agent-devkit-home-"));
    const projectDirectory = await mkdtemp(join(tmpdir(), "agent-devkit-project-"));

    try {
      const report = await new RunDoctor({
        appVersion: "0.4.0",
        systemInfo: {
          cwd: () => projectDirectory,
          homeDirectory: () => homeDirectory,
          nodeVersion: () => "v20.0.0",
          platform: () => "test-platform",
          stdinIsTTY: () => true,
          stdoutIsTTY: () => false,
        },
        pathInspector: {
          exists: async () => false,
        },
      }).execute();

      expect(report.status).toBe("ok");
      expect(report.version).toBe("0.4.0");
      expect(report.node.version).toBe("v20.0.0");
      expect(report.runtime.globalState.path).toBe(join(homeDirectory, ".agent-devkit"));
      expect(report.runtime.globalState.exists).toBe(false);
      expect(report.runtime.projectState.path).toBe(join(projectDirectory, ".agent-devkit"));
      expect(report.runtime.projectState.exists).toBe(false);
    } finally {
      await rm(homeDirectory, { force: true, recursive: true });
      await rm(projectDirectory, { force: true, recursive: true });
    }
  });
});
