import { execFile } from "node:child_process";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
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

describe("agent secrets", () => {
  it("stores, lists, reveals and removes encrypted secrets without logging plaintext", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-cli-"));

    try {
      const saved = JSON.parse(
        (
          await runAgent(home, [
            "secrets",
            "set",
            "openai.apiKey",
            "--service",
            "openai",
            "--value",
            "sk-test-secret",
            "--json",
          ])
        ).stdout,
      );
      const listed = JSON.parse((await runAgent(home, ["secrets", "list", "--json"])).stdout);
      const revealed = JSON.parse(
        (await runAgent(home, ["secrets", "show", "openai.apiKey", "--reveal", "--json"])).stdout,
      );
      const vaultBeforeRemove = await readFile(
        join(home, ".agent-devkit", "secrets", "vault.json"),
        "utf8",
      );
      const removed = JSON.parse(
        (await runAgent(home, ["secrets", "remove", "openai.apiKey", "--json"])).stdout,
      );
      const logDirectory = join(home, ".agent-devkit", "logs");
      const logFiles = await readdir(logDirectory);

      if (logFiles.length === 0) {
        throw new Error("Expected log files to be created.");
      }

      const logs = (
        await Promise.all(logFiles.map((logFile) => readFile(join(logDirectory, logFile), "utf8")))
      ).join("\n");

      expect(saved).toMatchObject({ action: "set", secret: { name: "openai.apiKey" } });
      expect(JSON.stringify(saved)).not.toContain("sk-test-secret");
      expect(listed.secrets).toEqual([expect.objectContaining({ name: "openai.apiKey" })]);
      expect(revealed.secret.value).toBe("sk-test-secret");
      expect(removed).toMatchObject({ action: "remove", removed: true });
      expect(logs).not.toContain("sk-test-secret");
      expect(vaultBeforeRemove).not.toContain("sk-test-secret");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("rotates credentials and prints audit events without plaintext", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-cli-"));

    try {
      await runAgent(home, [
        "secrets",
        "set",
        "openai.apiKey",
        "--service",
        "openai",
        "--value",
        "sk-test-secret",
        "--json",
      ]);
      const rotated = JSON.parse(
        (
          await runAgent(home, [
            "secrets",
            "rotate",
            "openai.apiKey",
            "--value",
            "sk-rotated-secret",
            "--json",
          ])
        ).stdout,
      );
      const audit = JSON.parse(
        (await runAgent(home, ["secrets", "audit", "openai.apiKey", "--json"])).stdout,
      );
      const revealed = JSON.parse(
        (await runAgent(home, ["secrets", "show", "openai.apiKey", "--reveal", "--json"])).stdout,
      );

      expect(rotated).toMatchObject({
        action: "rotate",
        secret: { name: "openai.apiKey", value: "********" },
      });
      expect(audit).toMatchObject({
        action: "audit",
        events: [
          expect.objectContaining({ action: "created", name: "openai.apiKey" }),
          expect.objectContaining({ action: "rotated", name: "openai.apiKey" }),
        ],
      });
      expect(revealed.secret.value).toBe("sk-rotated-secret");
      expect(JSON.stringify(audit)).not.toContain("sk-test-secret");
      expect(JSON.stringify(audit)).not.toContain("sk-rotated-secret");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
