import { execFile } from "node:child_process";
import { chmod, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

async function createFakeNpm(root: string): Promise<string> {
  const bin = join(root, "bin");
  const npm = join(bin, "npm");

  await mkdir(bin, { recursive: true });
  await writeFile(
    npm,
    `#!/usr/bin/env node
const args = process.argv.slice(2);
if (args.join(" ") === "view agent-devkit versions --json") {
  console.log(JSON.stringify(["0.3.2", "0.4.0", "0.4.1", "0.4.2"]));
  process.exit(0);
}
if (args.join(" ") === "view agent-devkit dist-tags --json") {
  console.log(JSON.stringify({ latest: "0.4.2" }));
  process.exit(0);
}
if (args[0] === "install") {
  process.exit(0);
}
console.error("unexpected npm args: " + args.join(" "));
process.exit(1);
`,
  );
  await chmod(npm, 0o755);

  return bin;
}

describe("agent update", () => {
  it("prints a JSON dry-run plan from registry metadata", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-update-cli-"));

    try {
      const fakeBin = await createFakeNpm(home);
      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "update", "--latest", "--dry-run", "--json"],
        {
          env: {
            ...process.env,
            HOME: home,
            PATH: `${fakeBin}:${process.env.PATH ?? ""}`,
          },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.status).toBe("planned");
      expect(result.currentVersion).toBe("0.4.0");
      expect(result.selectedVersion).toBe("0.4.2");
      expect(result.command).toBe("npm install -g agent-devkit@0.4.2");
      expect(result.executed).toBe(false);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("accepts an explicit target version as an argument", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-update-cli-"));

    try {
      const fakeBin = await createFakeNpm(home);
      const { stdout } = await execFileAsync(
        tsxBin,
        [mainEntrypoint, "update", "0.4.1", "--dry-run", "--json"],
        {
          env: {
            ...process.env,
            HOME: home,
            PATH: `${fakeBin}:${process.env.PATH ?? ""}`,
          },
        },
      );
      const result = JSON.parse(stdout);

      expect(result.selectedVersion).toBe("0.4.1");
      expect(result.command).toBe("npm install -g agent-devkit@0.4.1");
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
