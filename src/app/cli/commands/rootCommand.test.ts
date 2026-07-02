import { execFile } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");
const sessionPattern = /Session: (ses_[a-f0-9]+)/;

async function runAgent(args: string[]) {
  return execFileAsync(tsxBin, [mainEntrypoint, ...args], {
    cwd: repoRoot,
    env: { ...process.env, HOME: repoRoot },
  });
}

describe("agent root command", () => {
  it.each([["-v"], ["--version"]])("prints the version with %s", async (flag) => {
    const { stdout } = await runAgent([flag]);

    expect(stdout.trim()).toBe("0.3.4");
  });

  it.each([["-h"], ["--help"]])("prints help with %s", async (flag) => {
    const { stdout } = await runAgent([flag]);

    expect(stdout).toContain("Uso: agent [options] [command] [prompt...]");
    expect(stdout).toContain("Comandos:");
    expect(stdout).toContain("imprime a versao atual");
    expect(stdout).toContain("exibe ajuda do comando");
    expect(stdout).not.toContain(" chat ");
  });

  it.each([["chat"], ["ask"]])("rejects removed %s command aliases", async (alias) => {
    await expect(runAgent([alias, "Planeje o mini brain."])).rejects.toMatchObject({
      stderr: expect.stringContaining('O comando "chat" foi removido. Use: agent "sua mensagem"'),
    });
  });

  it("uses root prompts as a continuous CLI conversation", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-root-chat-"));

    try {
      const first = await execFileAsync(tsxBin, [mainEntrypoint, "Planeje o mini brain."], {
        cwd: repoRoot,
        env: { ...process.env, HOME: home },
      });
      const second = await execFileAsync(tsxBin, [mainEntrypoint, "Continue a mesma conversa."], {
        cwd: repoRoot,
        env: { ...process.env, HOME: home },
      });
      const firstSession = first.stdout.match(sessionPattern)?.[1];
      const secondSession = second.stdout.match(sessionPattern)?.[1];

      expect(first.stdout).not.toContain("Agent:");
      expect(first.stdout).toContain("kit:");
      expect(first.stdout).toContain("Planeje o mini brain.");
      expect(firstSession).toMatch(/^ses_/);
      expect(first.stdout).toContain("Model:");
      expect(first.stdout).toContain("Tokens:");
      expect(second.stdout).not.toContain("Agent:");
      expect(second.stdout).toContain("Continue a mesma conversa.");
      expect(secondSession).toBe(firstSession);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
