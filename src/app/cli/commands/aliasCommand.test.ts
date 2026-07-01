import { execFile } from "node:child_process";
import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

async function runAgent(home: string, args: string[]) {
  return execFileAsync(tsxBin, [mainEntrypoint, ...args], {
    env: {
      ...process.env,
      HOME: home,
      PATH: `${join(home, ".agent-devkit", "bin")}:${process.env.PATH}`,
    },
  });
}

describe("agent alias", () => {
  it("sets and removes a user CLI alias", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-alias-cli-"));

    try {
      const set = JSON.parse((await runAgent(home, ["alias", "set", "kit", "--json"])).stdout);
      const status = JSON.parse((await runAgent(home, ["alias", "--json"])).stdout);
      const shim = await readFile(join(home, ".agent-devkit", "bin", "kit"), "utf8");
      const removed = JSON.parse((await runAgent(home, ["alias", "remove", "--json"])).stdout);

      expect(set).toMatchObject({
        alias: { enabled: true, name: "kit" },
        status: "configured",
      });
      expect(status).toMatchObject({ alias: { name: "kit" }, status: "view" });
      expect(shim).toContain("agent");
      expect(removed).toMatchObject({ status: "removed" });
      await expect(access(join(home, ".agent-devkit", "bin", "kit"))).rejects.toThrow();
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
