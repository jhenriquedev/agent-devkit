import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { access, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const packageJson = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
const entry = new URL(`../${packageJson.bin.agent}`, import.meta.url);
const expectedSurfaceFiles = ["knowledge.json", "loop.json", "prompt.json", "skill.json"];
const expectedModules = ["logs", "project", "secrets", "self", "user"];

async function run(command, args, options = {}) {
  return execFileAsync(command, args, {
    maxBuffer: 1024 * 1024 * 10,
    ...options,
  });
}

async function assertExists(path) {
  await access(path, constants.R_OK);
}

async function assertJsonCommand(bin, args, env) {
  const { stdout } = await run(bin, args, { env });
  return JSON.parse(stdout);
}

await assertExists(entry);

const entrySource = await readFile(entry, "utf8");

if (!entrySource.startsWith("#!/usr/bin/env node")) {
  throw new Error(`${packageJson.bin.agent} must start with a node shebang`);
}

if (packageJson.name !== "agent-devkit") {
  throw new Error(`Unexpected package name: ${packageJson.name}`);
}

if (packageJson.version !== "0.4.0") {
  throw new Error(`Unexpected package version: ${packageJson.version}`);
}

const root = await mkdtemp(join(tmpdir(), "agent-devkit-package-verify-"));

try {
  const packDirectory = join(root, "pack");
  const consumerDirectory = join(root, "consumer");
  const homeDirectory = join(root, "home");

  await mkdir(packDirectory, { recursive: true });
  await mkdir(consumerDirectory, { recursive: true });
  await mkdir(homeDirectory, { recursive: true });
  const { stdout: packOutput } = await run("npm", [
    "pack",
    "--json",
    "--pack-destination",
    packDirectory,
  ]);
  const [packResult] = JSON.parse(packOutput);
  const tarball = join(packDirectory, packResult.filename);

  await run("npm", ["init", "-y"], { cwd: consumerDirectory });
  await run("npm", ["install", "--ignore-scripts", "--no-audit", "--no-fund", tarball], {
    cwd: consumerDirectory,
  });

  const installedPackage = join(consumerDirectory, "node_modules", packageJson.name);
  const agentBin = join(
    consumerDirectory,
    "node_modules",
    ".bin",
    process.platform === "win32" ? "agent.cmd" : "agent",
  );
  const env = { ...process.env, HOME: homeDirectory };

  const { stdout: versionOutput } = await run(agentBin, ["--version"], { env });
  if (versionOutput.trim() !== packageJson.version) {
    throw new Error(`Unexpected binary version: ${versionOutput.trim()}`);
  }

  const doctor = await assertJsonCommand(agentBin, ["doctor", "--json"], env);
  if (doctor.version !== packageJson.version || doctor.runtime.globalState.exists !== false) {
    throw new Error("Packaged doctor smoke test returned an invalid report.");
  }

  try {
    await access(join(homeDirectory, ".agent-devkit"));
    throw new Error("Packaged doctor must not create global Agent DevKit state.");
  } catch (error) {
    if (error?.code !== "ENOENT") {
      throw error;
    }
  }

  const preferences = await assertJsonCommand(agentBin, ["preferences", "--json"], env);
  if (preferences.preferences.theme !== "default-purple") {
    throw new Error("Packaged preferences smoke test returned an invalid payload.");
  }

  for (const file of [
    "src/assets/i18n/pt-BR.json",
    "src/assets/i18n/en-US.json",
    "src/assets/themes/default-purple.json",
    "src/assets/design/kit.json",
    "src/assets/design/semantics.json",
    "src/assets/characters/kit/character.json",
    "src/assets/characters/kit/sprite.js",
    "src/assets/characters/yuki/character.json",
    "src/assets/characters/yuki/sprite.js",
  ]) {
    await assertExists(join(installedPackage, file));
  }

  for (const moduleId of expectedModules) {
    for (const surfaceFile of expectedSurfaceFiles) {
      await assertExists(join(installedPackage, "src/modules", moduleId, "surface", surfaceFile));
    }
  }
} finally {
  await rm(root, { force: true, recursive: true });
}

console.log(`Package ${packageJson.name}@${packageJson.version} verified.`);
