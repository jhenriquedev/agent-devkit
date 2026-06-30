import { execFile } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

describe("agent preferences", () => {
  it("prints user preferences and available themes as JSON", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "preferences", "--json"], {
        env: { ...process.env, HOME: home },
      });
      const result = JSON.parse(stdout);

      expect(result.preferences.theme).toBe("default-purple");
      expect(result.themes).toHaveLength(7);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("updates selected user theme from the CLI", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "preferences", "set-theme", "forest-teal", "--json"],
        {
          env: { ...process.env, HOME: home },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.status).toBe("updated");
      expect(result.preferences.theme).toBe("forest-teal");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("updates selected user theme with the update command", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "preferences", "update", "--theme", "ocean-blue", "--json"],
        {
          env: { ...process.env, HOME: home },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.status).toBe("updated");
      expect(result.preferences.theme).toBe("ocean-blue");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
