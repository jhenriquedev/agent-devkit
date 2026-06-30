import { execFile } from "node:child_process";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

describe("agent update", () => {
  it("prints a JSON dry-run plan from registry metadata", async () => {
    const { stdout } = await execFileAsync(
      tsxBin,
      [mainEntrypoint, "update", "--latest", "--dry-run", "--json"],
      {
        env: {
          ...process.env,
          AGENT_DEVKIT_TEST_NPM_VIEW: JSON.stringify({
            distTags: { latest: "0.4.2" },
            versions: ["0.3.2", "0.4.0", "0.4.1", "0.4.2"],
          }),
        },
      },
    );
    const result = JSON.parse(stdout);

    expect(result.status).toBe("planned");
    expect(result.currentVersion).toBe("0.4.0");
    expect(result.selectedVersion).toBe("0.4.2");
    expect(result.command).toBe("npm install -g agent-devkit@0.4.2");
    expect(result.executed).toBe(false);
  });

  it("accepts an explicit target version as an argument", async () => {
    const { stdout } = await execFileAsync(
      tsxBin,
      [mainEntrypoint, "update", "0.4.1", "--dry-run", "--json"],
      {
        env: {
          ...process.env,
          AGENT_DEVKIT_TEST_NPM_VIEW: JSON.stringify({
            distTags: { latest: "0.4.2" },
            versions: ["0.3.2", "0.4.0", "0.4.1", "0.4.2"],
          }),
        },
      },
    );
    const result = JSON.parse(stdout);

    expect(result.selectedVersion).toBe("0.4.1");
    expect(result.command).toBe("npm install -g agent-devkit@0.4.1");
  });
});
