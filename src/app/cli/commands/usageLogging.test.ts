import { execFile } from "node:child_process";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

describe("agent usage logging", () => {
  it("writes a json usage log for successful CLI commands", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-logs-"));

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "preferences", "--json"], {
        env: { ...process.env, HOME: home },
      });
      const preferences = JSON.parse(stdout);

      expect(preferences.preferences.theme).toBe("default-purple");

      const logDirectory = join(home, ".agent-devkit", "logs");
      const [logFile] = await readdir(logDirectory);
      if (logFile === undefined) {
        throw new Error("Expected usage log file to be created.");
      }
      const content = await readFile(join(logDirectory, logFile), "utf8");
      const event = JSON.parse(content.trim());

      expect(event).toMatchObject({
        area: "user",
        argv: ["preferences", "--json"],
        category: "usage",
        command: "preferences",
        interface: "cli",
        level: "info",
        options: { json: true },
        schema: "agent-devkit.usage-log/v1",
        status: "succeeded",
      });
      expect(typeof event.durationMs).toBe("number");
      expect(event.durationMs).toBeGreaterThanOrEqual(0);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
