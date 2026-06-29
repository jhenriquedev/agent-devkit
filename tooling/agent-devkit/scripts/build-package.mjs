#!/usr/bin/env node

import { cp, mkdir, readdir, rm, stat, chmod } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(packageRoot, "..", "..");
const runtimeRoot = path.join(packageRoot, "runtime");

const topLevelIncludes = [
  "agent",
  "ai-devkit",
  "aikit",
  "cli",
  "agents",
  "providers",
  "plugins",
  "models",
  "vendor",
  "scripts",
  "tooling/toolchain.yaml",
  "workflows",
  "requirements.txt",
  "AGENTS.md",
  "LICENSE",
  "README.md",
  ".env.example",
];

const ignoredNames = new Set([
  ".git",
  ".github",
  "docs",
  "node_modules",
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  ".venv",
  "venv",
  "env",
  "logs",
  "tmp",
  ".cache",
  "coverage",
  "dist",
  "build",
  ".DS_Store",
]);

function shouldIgnore(sourcePath) {
  const name = path.basename(sourcePath);
  if (ignoredNames.has(name)) return true;
  if (name.endsWith(".pyc") || name.endsWith(".pyo")) return true;
  if (name === ".env" || (name.startsWith(".env.") && name !== ".env.example")) return true;
  if (sourcePath.startsWith(runtimeRoot)) return true;
  return false;
}

async function copyFiltered(source, target) {
  if (shouldIgnore(source)) return;
  const sourceStat = await stat(source);
  if (sourceStat.isDirectory()) {
    await mkdir(target, { recursive: true });
    const entries = await readdir(source);
    for (const entry of entries) {
      await copyFiltered(path.join(source, entry), path.join(target, entry));
    }
    return;
  }
  await mkdir(path.dirname(target), { recursive: true });
  await cp(source, target, { preserveTimestamps: true });
}

async function main() {
  await rm(runtimeRoot, { recursive: true, force: true });
  await mkdir(runtimeRoot, { recursive: true });

  for (const entry of topLevelIncludes) {
    const source = path.join(repoRoot, entry);
    try {
      await stat(source);
    } catch {
      continue;
    }
    await copyFiltered(source, path.join(runtimeRoot, entry));
  }

  for (const executable of ["agent", "ai-devkit", "aikit"]) {
    try {
      await chmod(path.join(runtimeRoot, executable), 0o755);
    } catch {
      // Optional compatibility executable may be absent during intermediate development.
    }
  }

  console.log(`Agent DevKit runtime packaged at ${runtimeRoot}`);
}

try {
  await main();
} catch (error) {
  console.error(error instanceof Error ? error.message : "Failed to build Agent DevKit npm package.");
  process.exit(1);
}
