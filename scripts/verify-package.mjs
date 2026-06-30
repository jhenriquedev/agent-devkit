import { constants } from "node:fs";
import { access, readFile } from "node:fs/promises";

const packageJson = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
const entry = new URL(`../${packageJson.bin.agent}`, import.meta.url);

await access(entry, constants.R_OK);

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

console.log(`Package ${packageJson.name}@${packageJson.version} verified.`);
