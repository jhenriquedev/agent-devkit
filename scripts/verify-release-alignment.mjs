#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");

function normalizeVersion(input) {
  return input.startsWith("v") ? input.slice(1) : input;
}

async function readJson(relativePath) {
  return JSON.parse(await readFile(path.join(repoRoot, relativePath), "utf8"));
}

async function readText(relativePath) {
  return readFile(path.join(repoRoot, relativePath), "utf8");
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`${label} mismatch: expected "${expected}", got "${actual}".`);
  }
}

function assertIncludes(content, needle, label) {
  if (!content.includes(needle)) {
    throw new Error(`${label} missing required content: ${needle}`);
  }
}

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: repoRoot,
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

async function main() {
  const [rawVersion] = process.argv.slice(2);
  if (!rawVersion) {
    throw new Error("Usage: npm run release:verify -- v0.0.3");
  }

  const version = normalizeVersion(rawVersion);
  const rootPackage = await readJson("package.json");
  const npmPackage = await readJson("tooling/agent-devkit/package.json");
  const cliInit = await readText("cli/aikit/__init__.py");
  const license = await readText("LICENSE");
  const readme = await readText("README.md");
  const releaseNotes = await readText("RELEASE_NOTES.md");

  assertEqual(rootPackage.version, version, "Root package version");
  assertEqual(rootPackage.license, "MIT", "Root package license");
  assertEqual(npmPackage.version, version, "npm package version");
  assertEqual(npmPackage.license, "MIT", "npm package license");
  assertIncludes(cliInit, `__version__ = "${version}"`, "cli/aikit/__init__.py");
  assertIncludes(license, "MIT License", "LICENSE");
  assertIncludes(license, "Agent DevKit contributors", "LICENSE");
  assertIncludes(readme, "agent-devkit", "README.md");
  assertIncludes(readme, "Comando canonico da CLI: `agent`", "README.md");
  assertIncludes(releaseNotes, `v${version}`, "RELEASE_NOTES.md");

  const versionResult = await run("python3", ["agent", "--version"]);
  assertEqual(versionResult.stdout.trim(), `agent ${version}`, "agent --version");

  await run("python3", ["scripts/validate-repo.py", "--strict"]);
  console.log(`release alignment verified for v${version}`);
}

try {
  await main();
} catch (error) {
  console.error(error instanceof Error ? error.message : "Release alignment verification failed.");
  process.exit(1);
}
