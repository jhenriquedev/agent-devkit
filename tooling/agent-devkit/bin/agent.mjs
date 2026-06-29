#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { accessSync, constants, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(__dirname, "..");
const runtimeRoot = path.join(packageRoot, "runtime");
const runtimeAgent = path.join(runtimeRoot, "agent");
const runtimeRequirements = path.join(runtimeRoot, "requirements.txt");
const packageJson = JSON.parse(readFileSync(path.join(packageRoot, "package.json"), "utf8"));

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
  const basePython = canExecute("python3") ? "python3" : (canExecute("python") ? "python" : null);
  if (!basePython) {
    return null;
  }
  if (!existsSync(runtimeRequirements)) {
    return basePython;
  }
  return ensureBundledPython(basePython);
}

function resolveAppHome() {
  if (process.env.AGENT_DEVKIT_HOME) return process.env.AGENT_DEVKIT_HOME;
  if (process.env.AI_DEVKIT_CONFIG_HOME) return process.env.AI_DEVKIT_CONFIG_HOME;
  if (process.env.AIKIT_CONFIG_HOME) return process.env.AIKIT_CONFIG_HOME;
  return path.join(os.homedir(), ".agent-devkit");
}

function venvPythonPath(venvRoot) {
  if (process.platform === "win32") {
    return path.join(venvRoot, "Scripts", "python.exe");
  }
  return path.join(venvRoot, "bin", "python");
}

function runOrFail(command, args, message, options = {}) {
  const result = spawnSync(command, args, {
    stdio: ["ignore", "pipe", "pipe"],
    shell: false,
    text: true,
    ...options,
  });
  if (result.status === 0) {
    return result;
  }
  const details = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
  throw new Error(`${message}${details ? `\n${details}` : ""}`);
}

function commandOk(command, args) {
  const result = spawnSync(command, args, {
    stdio: "ignore",
    shell: false,
  });
  return result.status === 0;
}

function canAutoInstallPythonVenv() {
  return (
    process.platform === "linux"
    && typeof process.getuid === "function"
    && process.getuid() === 0
    && process.env.AGENT_DEVKIT_DISABLE_SYSTEM_BOOTSTRAP !== "1"
    && canExecute("apt-get")
  );
}

function tryInstallPythonVenvPackage() {
  if (!canAutoInstallPythonVenv()) {
    return false;
  }
  if (!commandOk("apt-get", ["update"])) {
    return false;
  }
  return commandOk("apt-get", ["install", "-y", "python3-venv"]);
}

function createVenv(basePython, venvRoot) {
  const result = spawnSync(basePython, ["-m", "venv", venvRoot], {
    stdio: ["ignore", "pipe", "pipe"],
    shell: false,
    text: true,
  });
  if (result.status === 0) {
    return;
  }
  if (tryInstallPythonVenvPackage()) {
    runOrFail(basePython, ["-m", "venv", venvRoot], "Failed to create Agent DevKit Python environment.");
    return;
  }
  const details = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
  throw new Error(`Failed to create Agent DevKit Python environment.${details ? `\n${details}` : ""}`);
}

function pythonImportsOk(python) {
  const result = spawnSync(
    python,
    ["-c", "import yaml, jsonschema, bs4, pypdf, reportlab, llama_cpp"],
    { stdio: "ignore", shell: false },
  );
  return result.status === 0;
}

function ensureBundledPython(basePython) {
  const appHome = resolveAppHome();
  const venvRoot = process.env.AGENT_DEVKIT_PYTHON_ENV || path.join(appHome, "python");
  const python = venvPythonPath(venvRoot);
  const marker = path.join(venvRoot, ".agent-devkit-deps.json");
  mkdirSync(appHome, { recursive: true });

  if (!existsSync(python)) {
    createVenv(basePython, venvRoot);
  }
  if (pythonImportsOk(python) && markerMatches(marker)) {
    return python;
  }
  runOrFail(
    python,
    ["-m", "pip", "install", "--upgrade", "pip", "-r", runtimeRequirements],
    "Failed to install Agent DevKit Python dependencies.",
  );
  writeFileSync(marker, JSON.stringify({ version: packageJson.version, requirements: "runtime/requirements.txt" }, null, 2));
  return python;
}

function markerMatches(marker) {
  if (!existsSync(marker)) {
    return false;
  }
  try {
    const payload = JSON.parse(readFileSync(marker, "utf8"));
    return payload.version === packageJson.version;
  } catch {
    return false;
  }
}

try {
  accessSync(runtimeAgent, constants.R_OK);
} catch {
  console.error(`Agent DevKit runtime not found at ${runtimeAgent}. Reinstall the npm package.`);
  process.exit(1);
}

let python = null;
try {
  python = resolvePython();
} catch (error) {
  console.error(error instanceof Error ? error.message : "Agent DevKit Python bootstrap failed.");
  process.exit(1);
}
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
