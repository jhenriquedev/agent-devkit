import { execFile } from "node:child_process";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

async function runAgent(home: string, args: string[]) {
  return execFileAsync(tsxBin, [mainEntrypoint, ...args], {
    env: { ...process.env, HOME: home },
  });
}

async function readTechnicalLog(home: string): Promise<string> {
  const logDirectory = join(home, ".agent-devkit", "logs");
  const logFiles = await readdir(logDirectory);
  const technicalLogFile = logFiles.find((file) => file.startsWith("technical-"));

  if (technicalLogFile === undefined) {
    throw new Error("Expected technical log file to be created.");
  }

  return readFile(join(logDirectory, technicalLogFile), "utf8");
}

describe("agent technical logging", () => {
  it("writes redacted technical audit logs for successful CLI commands", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-technical-cli-"));

    try {
      await runAgent(home, [
        "secrets",
        "set",
        "openai.apiKey",
        "--service",
        "openai",
        "--value",
        "sk-test-secret",
        "--json",
      ]);

      const content = await readTechnicalLog(home);
      const events = content
        .trim()
        .split("\n")
        .map((line) => JSON.parse(line));

      expect(events).toEqual([
        expect.objectContaining({
          category: "technical",
          command: "secrets.set",
          event: "command.started",
          level: "info",
          schema: "agent-devkit.technical-log/v1",
        }),
        expect.objectContaining({
          category: "technical",
          command: "secrets.set",
          durationMs: expect.any(Number),
          event: "command.succeeded",
          level: "info",
          schema: "agent-devkit.technical-log/v1",
        }),
      ]);
      expect(content).toContain("[redacted]");
      expect(content).not.toContain("sk-test-secret");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("writes technical audit logs for failed CLI commands", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-technical-cli-"));

    try {
      let failed = false;
      try {
        await runAgent(home, ["secrets", "show", "missing.secret", "--json"]);
      } catch {
        failed = true;
      }
      expect(failed).toBe(true);

      const content = await readTechnicalLog(home);
      const events = content
        .trim()
        .split("\n")
        .map((line) => JSON.parse(line));

      expect(events).toContainEqual(
        expect.objectContaining({
          category: "technical",
          command: "secrets.show",
          durationMs: expect.any(Number),
          error: expect.objectContaining({ name: "Error" }),
          event: "command.failed",
          level: "error",
          schema: "agent-devkit.technical-log/v1",
        }),
      );
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
