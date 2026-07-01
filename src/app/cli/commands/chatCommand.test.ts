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

describe("agent chat", () => {
  it("sends a chat message and persists it in a session", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-chat-cli-"));

    try {
      const result = JSON.parse(
        (await runAgent(home, ["chat", "--json", "Planeje o mini brain."])).stdout,
      );

      expect(result).toMatchObject({
        action: "send",
        reply: expect.stringContaining("Planeje o mini brain."),
        sessionId: expect.stringMatching(/^ses_/),
      });
      expect(result.messages).toEqual([
        expect.objectContaining({ role: "user" }),
        expect.objectContaining({ role: "assistant" }),
      ]);
      expect(result.prompt).toMatchObject({
        schema: "agent-devkit.prompt/v1",
        policies: { allowToolCalls: false },
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
