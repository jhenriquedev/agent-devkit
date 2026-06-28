#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { accessSync, constants } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(__dirname, "..");
const runtimeRoot = path.join(packageRoot, "runtime");
const runtimeAgent = path.join(runtimeRoot, "agent");

function canExecute(command) {
  const result = spawnSync(command, ["--version"], {
    stdio: "ignore",
    shell: false,
  });
  return result.status === 0;
}

function resolvePython() {
  if (process.env.AGENT_DEVKIT_PYTHON) {
    return process.env.AGENT_DEVKIT_PYTHON;
  }
  if (canExecute("python3")) {
    return "python3";
  }
  if (canExecute("python")) {
    return "python";
  }
  return null;
}

try {
  accessSync(runtimeAgent, constants.R_OK);
} catch {
  console.error(`Agent DevKit runtime not found at ${runtimeAgent}. Reinstall the npm package.`);
  process.exit(1);
}

const python = resolvePython();
if (!python) {
  console.error("Agent DevKit requires Python 3.11+ available as python3 or python.");
  console.error("Set AGENT_DEVKIT_PYTHON to a Python executable if it is installed in a custom location.");
  process.exit(1);
}

const child = spawnSync(python, [runtimeAgent, ...process.argv.slice(2)], {
  stdio: "inherit",
  shell: false,
  env: {
    ...process.env,
    AI_DEVKIT_ROOT: runtimeRoot,
    PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE ?? "1",
  },
});

if (child.error) {
  console.error(child.error.message);
  process.exit(1);
}

process.exit(child.status ?? 1);
