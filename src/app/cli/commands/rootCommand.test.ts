import { execFile } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

async function runAgent(args: string[]) {
  return execFileAsync(tsxBin, [mainEntrypoint, ...args], {
    cwd: repoRoot,
    env: { ...process.env, HOME: repoRoot },
  });
}

describe("agent root command", () => {
  it.each([["-v"], ["--version"]])("prints the version with %s", async (flag) => {
    const { stdout } = await runAgent([flag]);

    expect(stdout.trim()).toBe("0.4.0");
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

  it("uses a root prompt as a user conversation message", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-root-chat-"));

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "Planeje o mini brain."], {
        cwd: repoRoot,
        env: { ...process.env, HOME: home },
      });

      expect(stdout).toContain("Agent:");
      expect(stdout).toContain("Planeje o mini brain.");
      expect(stdout).toContain("Session: ses_");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
