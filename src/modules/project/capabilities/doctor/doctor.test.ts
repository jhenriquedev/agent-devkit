import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Result } from "../../../../infra/bases/result";
import type { DoctorReport } from "./doctor.entities";
import { DoctorService } from "./doctor.service";
import { formatDoctorText } from "./doctor.viewmodel";

describe("project.doctor", () => {
  it("reports environment state without creating Agent DevKit directories", async () => {
    const homeDirectory = await mkdtemp(join(tmpdir(), "agent-devkit-home-"));
    const projectDirectory = await mkdtemp(join(tmpdir(), "agent-devkit-project-"));

    try {
      const result = await new DoctorService({
        appVersion: "0.4.0",
        repository: {
          repositoryId: "test.doctor.repository",
          cwd: () => Result.ok(projectDirectory),
          exists: async () => Result.ok(false),
          homeDirectory: () => Result.ok(homeDirectory),
          nodeVersion: () => Result.ok("v20.0.0"),
          platform: () => Result.ok("test-platform"),
          stdinIsTTY: () => Result.ok(true),
          stdoutIsTTY: () => Result.ok(false),
        },
      }).execute();

      expect(result.isOk()).toBe(true);
      const report = result.unwrap();

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

  it("formats a branded terminal-style doctor report", () => {
    const report: DoctorReport = {
      status: "ok",
      version: "0.4.0",
      node: {
        version: "v20.0.0",
      },
      system: {
        platform: "test-platform",
        cwd: "/workspace/project",
      },
      terminal: {
        stdinIsTTY: true,
        stdoutIsTTY: false,
      },
      runtime: {
        globalState: {
          path: "/home/user/.agent-devkit",
          exists: false,
        },
        projectState: {
          path: "/workspace/project/.agent-devkit",
          exists: true,
        },
      },
    };

    const output = formatDoctorText(report, { color: false });

    expect(output).toContain("Agent DevKit Doctor");
    expect(output).toContain("local - no credentials required");
    expect(output).toContain("> agent doctor");
    expect(output).toContain("[ok] local health");
    expect(output).toContain("runtime");
    expect(output).toContain("environment");
    expect(output).toContain("state");
    expect(output).toContain("global  missing  /home/user/.agent-devkit");
    expect(output).toContain("project found    /workspace/project/.agent-devkit");
  });

  it("can apply brand colors when terminal color is enabled", () => {
    const report: DoctorReport = {
      status: "ok",
      version: "0.4.0",
      node: {
        version: "v20.0.0",
      },
      system: {
        platform: "test-platform",
        cwd: "/workspace/project",
      },
      terminal: {
        stdinIsTTY: true,
        stdoutIsTTY: true,
      },
      runtime: {
        globalState: {
          path: "/home/user/.agent-devkit",
          exists: false,
        },
        projectState: {
          path: "/workspace/project/.agent-devkit",
          exists: false,
        },
      },
    };

    expect(formatDoctorText(report, { color: true })).toContain("\u001b[38;2;139;122;230m");
  });
});
