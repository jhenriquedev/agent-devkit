import { execFile } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
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

describe("agent sessions", () => {
  it("creates, appends, searches and resumes sessions as JSON", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-sessions-cli-"));

    try {
      const created = JSON.parse(
        (await runAgent(home, ["sessions", "create", "--title", "Context planning", "--json"]))
          .stdout,
      );
      const sessionId = created.session.id;

      const appended = JSON.parse(
        (
          await runAgent(home, [
            "sessions",
            "append",
            sessionId,
            "--role",
            "user",
            "--content",
            "Quero memoria de sessoes",
            "--json",
          ])
        ).stdout,
      );
      const searched = JSON.parse(
        (await runAgent(home, ["session", "search", "memoria", "--json"])).stdout,
      );
      const resumed = JSON.parse(
        (await runAgent(home, ["sessions", "resume", sessionId, "--json"])).stdout,
      );

      expect(created).toMatchObject({
        action: "create",
        session: { title: "Context planning" },
      });
      expect(appended).toMatchObject({
        action: "append-message",
        message: { content: "Quero memoria de sessoes" },
      });
      expect(searched).toMatchObject({
        action: "search",
        results: [expect.objectContaining({ sessionId })],
      });
      expect(resumed).toMatchObject({
        action: "resume",
        messages: [expect.objectContaining({ content: "Quero memoria de sessoes" })],
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("prints human-readable session output", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-sessions-cli-"));

    try {
      await runAgent(home, ["sessions", "create", "--title", "Context planning"]);
      const { stdout } = await runAgent(home, ["sessions"]);

      expect(stdout).toContain("Agent DevKit Sessions");
      expect(stdout).toContain("Context planning");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
