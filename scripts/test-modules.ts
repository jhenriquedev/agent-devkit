import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import type { AgentDevKitModuleConfig } from "../src/infra/bases/module";
import { projectModuleConfig } from "../src/modules/project/project.config";
import { selfModuleConfig } from "../src/modules/self/self.config";
import { userModuleConfig } from "../src/modules/user/user.config";

const moduleConfigs: AgentDevKitModuleConfig[] = [
  projectModuleConfig,
  selfModuleConfig,
  userModuleConfig,
];

function printUsage(): void {
  console.log("Usage: npm run test:modules -- [module...] [--changed]");
  console.log(`Known modules: ${moduleConfigs.map((moduleConfig) => moduleConfig.id).join(", ")}`);
}

function changedModuleIds(): Set<string> {
  const result = spawnSync(
    "git",
    ["status", "--porcelain", "--untracked-files=all", "--", "src/modules"],
    {
      encoding: "utf8",
    },
  );

  if (result.status !== 0) {
    return new Set();
  }

  const changedPaths = result.stdout
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.slice(3))
    .map((path) => path.split(" -> ").at(-1) ?? path);

  return new Set(
    moduleConfigs
      .filter((moduleConfig) =>
        changedPaths.some((path) => path.startsWith(`src/modules/${moduleConfig.id}/`)),
      )
      .map((moduleConfig) => moduleConfig.id),
  );
}

function selectModules(args: string[]): AgentDevKitModuleConfig[] {
  const knownModules = new Map(
    moduleConfigs.map((moduleConfig) => [moduleConfig.id, moduleConfig]),
  );
  const changedOnly = args.includes("--changed");
  const selectedIds = args.filter((arg) => !arg.startsWith("-"));

  if (changedOnly) {
    const changedIds = changedModuleIds();
    return moduleConfigs.filter((moduleConfig) => changedIds.has(moduleConfig.id));
  }

  if (selectedIds.length === 0) {
    return moduleConfigs;
  }

  const unknownIds = selectedIds.filter((moduleId) => !knownModules.has(moduleId));
  if (unknownIds.length > 0) {
    console.error(`Unknown module: ${unknownIds.join(", ")}`);
    printUsage();
    process.exit(1);
  }

  return selectedIds.flatMap((moduleId) => {
    const moduleConfig = knownModules.get(moduleId);
    return moduleConfig === undefined ? [] : [moduleConfig];
  });
}

function walkFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);

    if (entry.isDirectory()) {
      return walkFiles(path);
    }

    return statSync(path).isFile() ? [path] : [];
  });
}

function expandTestInclude(pattern: string): string[] {
  if (!pattern.includes("*")) {
    return existsSync(pattern) ? [pattern] : [];
  }

  const [rootDirectory, filePattern] = pattern.split("/**/");
  if (rootDirectory === undefined || filePattern === undefined || !existsSync(rootDirectory)) {
    return [];
  }

  const suffix = filePattern.replace("*", "");
  return walkFiles(rootDirectory)
    .filter((path) => path.endsWith(suffix))
    .sort();
}

function runModuleTests(moduleConfig: AgentDevKitModuleConfig): number {
  const vitestBin = join(
    process.cwd(),
    "node_modules",
    ".bin",
    process.platform === "win32" ? "vitest.cmd" : "vitest",
  );
  const testFiles = moduleConfig.tests.include.flatMap((pattern) => expandTestInclude(pattern));
  const args = ["run", ...testFiles];

  console.log(`\n[${moduleConfig.id}] vitest ${args.join(" ")}`);

  const result = spawnSync(vitestBin, args, {
    stdio: "inherit",
  });

  return result.status ?? 1;
}

const modulesToTest = selectModules(process.argv.slice(2));

if (modulesToTest.length === 0) {
  console.log("No changed modules with bound tests.");
  process.exit(0);
}

for (const moduleConfig of modulesToTest) {
  const status = runModuleTests(moduleConfig);
  if (status !== 0) {
    process.exit(status);
  }
}
