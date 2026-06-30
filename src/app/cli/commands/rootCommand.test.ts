import { execFile } from "node:child_process";
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
  });
});
