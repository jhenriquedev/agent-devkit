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

describe("agent projects", () => {
  it("creates, lists and shows context projects as JSON", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-projects-cli-"));

    try {
      const created = JSON.parse(
        (
          await runAgent(home, [
            "projects",
            "create",
            "--name",
            "Agent DevKit",
            "--path",
            ".",
            "--tags",
            "typescript,cli",
            "--json",
          ])
        ).stdout,
      );
      const listed = JSON.parse((await runAgent(home, ["projects", "--json"])).stdout);
      const shown = JSON.parse(
        (await runAgent(home, ["project", "show", "proj_agent_devkit", "--json"])).stdout,
      );

      expect(created).toMatchObject({
        action: "create",
        project: { id: "proj_agent_devkit", name: "Agent DevKit" },
      });
      expect(listed).toMatchObject({
        action: "list",
        projects: [expect.objectContaining({ id: "proj_agent_devkit" })],
      });
      expect(shown).toMatchObject({
        action: "show",
        project: { tags: ["typescript", "cli"] },
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("prints human-readable project output", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-projects-cli-"));

    try {
      await runAgent(home, ["projects", "create", "--name", "Agent DevKit"]);
      const { stdout } = await runAgent(home, ["projects"]);

      expect(stdout).toContain("Agent DevKit Projects");
      expect(stdout).toContain("proj_agent_devkit");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
