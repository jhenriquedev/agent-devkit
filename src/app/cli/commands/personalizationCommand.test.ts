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
    env: { ...process.env, HOME: home },
  });
}

describe("agent personalization", () => {
  it("views, updates and resets the local agent profile", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-cli-"));

    try {
      const initial = JSON.parse((await runAgent(home, ["personalization", "--json"])).stdout);

      expect(initial).toMatchObject({
        characters: expect.arrayContaining([
          expect.objectContaining({
            id: "yuki",
            profile: expect.objectContaining({
              behavior: "pragmatic",
              detailLevel: "technical",
              tone: "formal",
            }),
          }),
        ]),
        profile: {
          currentCharacter: {
            id: "kit",
          },
        },
        status: "view",
      });

      const updated = JSON.parse(
        (
          await runAgent(home, [
            "personalize",
            "update",
            "--name",
            "Robot",
            "--character",
            "robot",
            "--behavior",
            "pragmatic",
            "--tone",
            "neutral",
            "--detail",
            "technical",
            "--traits",
            "technical,precise",
            "--json",
          ])
        ).stdout,
      );

      expect(updated).toMatchObject({
        profile: {
          currentCharacter: {
            id: "robot",
            name: "Robot",
            profile: {
              traits: ["technical", "precise"],
            },
          },
        },
        status: "updated",
      });

      const persisted = JSON.parse(
        await readFile(
          join(home, ".agent-devkit", "data", "personalization", "profile.json"),
          "utf8",
        ),
      );

      expect(persisted.currentCharacter.name).toBe("Robot");

      const reset = JSON.parse(
        (await runAgent(home, ["personalization", "reset-defaults", "--json"])).stdout,
      );

      expect(reset).toMatchObject({
        profile: {
          currentCharacter: {
            id: "kit",
          },
        },
        status: "reset",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("rejects invalid enum values without corrupting the saved profile", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-personalization-cli-"));

    try {
      await expect(
        runAgent(home, ["personalize", "update", "--behavior", "banana", "--json"]),
      ).rejects.toMatchObject({
        stderr: expect.stringContaining("INVALID_INPUT"),
      });

      await expect(
        access(join(home, ".agent-devkit", "data", "personalization", "profile.json")),
      ).rejects.toMatchObject({ code: "ENOENT" });

      const view = JSON.parse((await runAgent(home, ["personalization", "--json"])).stdout);

      expect(view.profile.currentCharacter.profile.behavior).toBe("balanced");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
