import { execFile } from "node:child_process";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { ErrorCodes } from "../../../infra/bases/errors";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

async function runAgent(home: string, args: string[]) {
  return execFileAsync(tsxBin, [mainEntrypoint, ...args], {
    env: { ...process.env, HOME: home },
  });
}

async function runAgentExpectFailure(home: string, args: string[]) {
  try {
    await runAgent(home, args);
  } catch (error) {
    return error as { stderr: string; stdout: string };
  }

  throw new Error("Expected command to fail.");
}

describe("agent tools/run", () => {
  it("lists tools as machine-readable JSON", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-tools-cli-"));

    try {
      const { stdout } = await runAgent(home, ["tools", "--json"]);
      const result = JSON.parse(stdout);

      expect(result.tools).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            id: "context.projects",
            inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
            risk: "writes-global-state",
          }),
          expect.objectContaining({
            id: "context.sessions",
            inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
            risk: "writes-global-state",
          }),
          expect.objectContaining({
            id: "project.doctor",
            inputSchema: expect.objectContaining({ type: "object" }),
            risk: "read-only",
          }),
          expect.objectContaining({
            id: "user.personalization",
            inputSchema: expect.objectContaining({ oneOf: expect.any(Array) }),
            risk: "writes-global-state",
          }),
        ]),
      );
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("runs a read-only capability through the tool runtime", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-run-cli-"));

    try {
      const { stdout } = await runAgent(home, ["run", "project.doctor", "--input", "{}", "--json"]);
      const result = JSON.parse(stdout);

      expect(result).toMatchObject({
        capabilityId: "project.doctor",
        output: { version: "0.3.3" },
        status: "succeeded",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("runs the environment dependencies capability through the tool runtime", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-run-cli-"));

    try {
      const { stdout } = await runAgent(home, [
        "run",
        "environment.dependencies",
        "--input",
        '{"action":"verify","dependency":"node"}',
        "--json",
      ]);
      const result = JSON.parse(stdout);

      expect(result).toMatchObject({
        capabilityId: "environment.dependencies",
        output: {
          action: "verify",
          dependency: "node",
          status: "ok",
        },
        status: "succeeded",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("returns non-zero and a structured payload when approval is required", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-run-cli-"));

    try {
      const error = await runAgentExpectFailure(home, [
        "run",
        "project.reset",
        "--input",
        JSON.stringify({
          confirmed: true,
          dryRun: false,
          homeDirectory: home,
          projectRoot: home,
          scope: "project",
        }),
        "--json",
      ]);
      const result = JSON.parse(error.stdout);

      expect(result).toMatchObject({
        capabilityId: "project.reset",
        error: { code: ErrorCodes.ApprovalRequired },
        status: "approval_required",
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("rejects invalid JSON input", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-run-cli-"));

    try {
      const error = await runAgentExpectFailure(home, [
        "run",
        "project.doctor",
        "--input",
        "{",
        "--json",
      ]);

      expect(error.stderr).toContain("Invalid JSON passed to --input.");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("redacts raw JSON input from run command usage and technical logs", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-run-cli-"));

    try {
      await runAgent(home, [
        "run",
        "secrets.vault",
        "--input",
        JSON.stringify({
          action: "set",
          name: "openai.apiKey",
          service: "openai",
          value: "SEGREDO",
        }),
        "--approve",
        "--json",
      ]);

      const logDirectory = join(home, ".agent-devkit", "data", "logs");
      const logFiles = await readdir(logDirectory);
      const logs = (
        await Promise.all(logFiles.map((logFile) => readFile(join(logDirectory, logFile), "utf8")))
      ).join("\n");

      expect(logs).not.toContain("SEGREDO");
      expect(logs).toContain("[redacted]");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
