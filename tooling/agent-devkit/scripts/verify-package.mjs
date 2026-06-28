#!/usr/bin/env node

import { mkdtemp, rm, readdir, stat } from "node:fs/promises";
import { spawn } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(__dirname, "..");
const runtimeRoot = path.join(packageRoot, "runtime");
const agentBin = path.join(packageRoot, "bin", "agent.mjs");
const forbiddenNames = new Set([".git", "docs", "node_modules", "__pycache__", ".pytest_cache"]);

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: packageRoot,
      shell: false,
      text: true,
      stdio: ["ignore", "pipe", "pipe"],
      ...options,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
        return;
      }
      reject(new Error(`${command} ${args.join(" ")} failed with ${code}\n${stdout}\n${stderr}`));
    });
  });
}

async function assertExists(relativePath) {
  await stat(path.join(runtimeRoot, relativePath));
}

async function assertNoForbiddenFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (forbiddenNames.has(entry.name)) {
      throw new Error(`Forbidden path found in npm runtime: ${fullPath}`);
    }
    if (entry.name === ".env" || (entry.name.startsWith(".env.") && entry.name !== ".env.example")) {
      throw new Error(`Forbidden env file found in npm runtime: ${fullPath}`);
    }
    if (entry.name.endsWith(".pyc") || entry.name.endsWith(".pyo")) {
      throw new Error(`Forbidden Python cache found in npm runtime: ${fullPath}`);
    }
    if (entry.isDirectory()) {
      await assertNoForbiddenFiles(fullPath);
    }
  }
}

async function main() {
  await assertExists("agent");
  await assertExists("cli/aikit/main.py");
  await assertExists("agents");
  await assertExists("providers");
  await assertExists("plugins");
  await assertNoForbiddenFiles(runtimeRoot);

  const configHome = await mkdtemp(path.join(os.tmpdir(), "agent-devkit-package-"));
  try {
    const env = {
      ...process.env,
      AIKIT_CONFIG_HOME: configHome,
      AI_DEVKIT_CONFIG_HOME: configHome,
      PYTHONDONTWRITEBYTECODE: "1",
    };
    const version = await run("node", [agentBin, "--version"], { env });
    if (!version.stdout.trim().startsWith("agent 0.0.1")) {
      throw new Error(`Unexpected version output: ${version.stdout}`);
    }
    const commands = await run("node", [agentBin, "commands", "list", "--json"], { env });
    const payload = JSON.parse(commands.stdout);
    const deterministic = new Set(payload.deterministic.map((item) => item.command));
    for (const command of ["agents", "capabilities", "run", "doctor", "install", "source", "memory"]) {
      if (!deterministic.has(command)) {
        throw new Error(`Missing deterministic command in package smoke: ${command}`);
      }
    }
    const doctor = await run("node", [agentBin, "doctor", "--json"], { env });
    const doctorPayload = JSON.parse(doctor.stdout);
    if (doctorPayload.status !== "ok") {
      throw new Error(`Packaged runtime doctor failed: ${doctor.stdout}`);
    }
    await assertNoForbiddenFiles(runtimeRoot);
  } finally {
    await rm(configHome, { recursive: true, force: true });
  }

  console.log("Agent DevKit npm package verified.");
}

try {
  await main();
} catch (error) {
  console.error(error instanceof Error ? error.message : "Agent DevKit package verification failed.");
  process.exit(1);
}
