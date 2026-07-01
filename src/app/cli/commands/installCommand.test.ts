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

describe("agent install", () => {
  it("plans dependency installation through the tool runtime", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-install-cli-"));

    try {
      const { stdout } = await runAgent(home, ["install", "node", "--dry-run", "--json"]);
      const result = JSON.parse(stdout);

      expect(result).toMatchObject({
        capabilityId: "environment.dependencies",
        output: {
          action: "plan-install",
          dependency: "node",
          status: "unsupported",
        },
        status: "succeeded",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("verifies a dependency through the install command", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-install-cli-"));

    try {
      const { stdout } = await runAgent(home, ["install", "node", "--verify", "--json"]);
      const result = JSON.parse(stdout);

      expect(result).toMatchObject({
        capabilityId: "environment.dependencies",
        output: {
          action: "verify",
          checks: [expect.objectContaining({ id: "node", status: "ok" })],
          dependency: "node",
          status: "ok",
        },
        status: "succeeded",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("supports the --node dependency alias", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-install-cli-"));

    try {
      const { stdout } = await runAgent(home, ["install", "--node", "--verify", "--json"]);
      const result = JSON.parse(stdout);

      expect(result.output.dependency).toBe("node");
      expect(result.output.status).toBe("ok");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
