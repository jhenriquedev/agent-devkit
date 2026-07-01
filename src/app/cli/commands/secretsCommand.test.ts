import { execFile, spawn } from "node:child_process";
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

function runAgentWithInput(
  home: string,
  args: string[],
  input: string,
): Promise<{ stderr: string; stdout: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(tsxBin, [mainEntrypoint, ...args], {
      env: { ...process.env, HOME: home },
      stdio: ["pipe", "pipe", "pipe"],
    });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];

    child.stdout.on("data", (chunk) => stdout.push(Buffer.from(chunk)));
    child.stderr.on("data", (chunk) => stderr.push(Buffer.from(chunk)));
    child.on("error", reject);
    child.on("close", (code) => {
      const output = {
        stderr: Buffer.concat(stderr).toString("utf8"),
        stdout: Buffer.concat(stdout).toString("utf8"),
      };

      if (code === 0) {
        resolve(output);
        return;
      }

      reject(new Error(output.stderr || output.stdout || `agent exited with code ${code}`));
    });
    child.stdin.end(input);
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
        join(home, ".agent-devkit", "data", "secrets", "vault.json"),
        "utf8",
      );
      const removed = JSON.parse(
        (await runAgent(home, ["secrets", "remove", "openai.apiKey", "--json"])).stdout,
      );
      const logDirectory = join(home, ".agent-devkit", "data", "logs");
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

  it("stores and rotates credentials from stdin", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-stdin-cli-"));

    try {
      const saved = JSON.parse(
        (
          await runAgentWithInput(
            home,
            ["secrets", "set", "openai.apiKey", "--service", "openai", "--stdin", "--json"],
            "sk-stdin-secret\n",
          )
        ).stdout,
      );
      const rotated = JSON.parse(
        (
          await runAgentWithInput(
            home,
            ["secrets", "rotate", "openai.apiKey", "--stdin", "--json"],
            "sk-stdin-rotated-secret\n",
          )
        ).stdout,
      );
      const revealed = JSON.parse(
        (await runAgent(home, ["secrets", "show", "openai.apiKey", "--reveal", "--json"])).stdout,
      );
      const logDirectory = join(home, ".agent-devkit", "data", "logs");
      const logFiles = await readdir(logDirectory);
      const logs = (
        await Promise.all(logFiles.map((logFile) => readFile(join(logDirectory, logFile), "utf8")))
      ).join("\n");

      expect(saved).toMatchObject({ action: "set", secret: { name: "openai.apiKey" } });
      expect(rotated).toMatchObject({ action: "rotate", secret: { name: "openai.apiKey" } });
      expect(revealed.secret.value).toBe("sk-stdin-rotated-secret");
      expect(logs).not.toContain("sk-stdin-secret");
      expect(logs).not.toContain("sk-stdin-rotated-secret");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("rejects ambiguous secret value sources", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-secrets-ambiguous-cli-"));

    try {
      await expect(
        runAgentWithInput(
          home,
          ["secrets", "set", "openai.apiKey", "--stdin", "--value", "sk-test-secret"],
          "sk-stdin-secret\n",
        ),
      ).rejects.toThrow("Use --stdin or --value, not both.");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
