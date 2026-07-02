import { readFile } from "node:fs/promises";

const expected = process.argv[2];

if (!expected) {
  throw new Error("Usage: npm run release:verify -- v0.3.4");
}

const packageJson = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
const normalized = expected.startsWith("v") ? expected.slice(1) : expected;

if (packageJson.version !== normalized) {
  throw new Error(`Release version ${expected} does not match package.json ${packageJson.version}`);
}

if (packageJson.name !== "agent-devkit") {
  throw new Error(`Unexpected package name: ${packageJson.name}`);
}

console.log(`Release alignment verified for ${packageJson.name}@${packageJson.version}.`);
