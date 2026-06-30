import { formatDoctorText } from "../src/app/viewmodels/doctorViewModel";
import type { DoctorReport } from "../src/domain/entities/DoctorReport";

describe("doctor view model", () => {
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
