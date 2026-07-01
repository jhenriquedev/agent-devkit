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
      expect(result.preferences.language).toBe("pt-BR");
      expect(result.preferences.logRetentionDays).toBe(30);
      expect(result.themes).toHaveLength(7);
      expect(result.languages).toHaveLength(5);
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

  it("updates selected user language from the CLI", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "preferences", "set-language", "fr-FR", "--json"],
        {
          env: { ...process.env, HOME: home },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.status).toBe("updated");
      expect(result.preferences.language).toBe("fr-FR");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("updates log retention from the CLI", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "preferences", "update", "--log-retention-days", "90", "--json"],
        {
          env: { ...process.env, HOME: home },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.status).toBe("updated");
      expect(result.preferences.logRetentionDays).toBe(90);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("rejects invalid log retention values before saving preferences", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      await expect(
        execFileAsync(tsxBin, [mainEntrypoint, "preferences", "set-log-retention", "abc"], {
          env: { ...process.env, HOME: home },
        }),
      ).rejects.toThrow("Expected a positive integer");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("restores default user preferences from the CLI", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      await execFileAsync(
        tsxBin,
        [
          mainEntrypoint,
          "preferences",
          "update",
          "--theme",
          "ocean-blue",
          "--language",
          "en-US",
          "--log-retention-days",
          "90",
        ],
        {
          env: { ...process.env, HOME: home },
        },
      );

      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "preferences", "reset-defaults", "--json"],
        {
          env: { ...process.env, HOME: home },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.status).toBe("reset");
      expect(result.preferences.theme).toBe("default-purple");
      expect(result.preferences.language).toBe("pt-BR");
      expect(result.preferences.logRetentionDays).toBe(30);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("prints preferences in the selected language", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-cli-home-"));

    try {
      await execFileAsync(
        tsxBin,
        [mainEntrypoint, "preferences", "set-language", "en-US", "--json"],
        {
          env: { ...process.env, HOME: home },
        },
      );

      const { stdout } = await execFileAsync(tsxBin, [mainEntrypoint, "preferences"], {
        env: { ...process.env, HOME: home },
      });

      expect(stdout).toContain("Agent DevKit Preferences");
      expect(stdout).toContain("language en-US");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
