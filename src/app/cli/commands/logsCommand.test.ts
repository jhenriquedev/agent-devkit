import { execFile } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const repoRoot = process.cwd();
const tsxBin = join(repoRoot, "node_modules", ".bin", "tsx");
const mainEntrypoint = join(repoRoot, "src", "main.tsx");

async function runAgent(home: string, args: string[]) {
  return execFileAsync(tsxBin, [mainEntrypoint, ...args], {
    env: { ...process.env, HOME: home },
  });
}

describe("agent logs", () => {
  it("lists, tails, searches and summarizes usage logs", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-cli-"));

    try {
      await runAgent(home, ["preferences", "--json"]);
      await runAgent(home, ["doctor", "--json"]);

      const list = JSON.parse((await runAgent(home, ["logs", "--json"])).stdout);
      const tail = JSON.parse(
        (await runAgent(home, ["logs", "tail", "--limit", "3", "--json"])).stdout,
      );
      const search = JSON.parse(
        (await runAgent(home, ["logs", "search", "preferences", "--json"])).stdout,
      );
      const summary = JSON.parse((await runAgent(home, ["logs", "summary", "--json"])).stdout);
      const technicalSearch = JSON.parse(
        (await runAgent(home, ["logs", "search", "command.started", "--technical", "--json"]))
          .stdout,
      );
      const allSummary = JSON.parse(
        (await runAgent(home, ["logs", "summary", "--all", "--json"])).stdout,
      );

      expect(list.action).toBe("list");
      expect(list.files[0].eventCount).toBeGreaterThanOrEqual(2);
      expect(tail.action).toBe("read");
      expect(tail.events.map((event: { command: string }) => event.command)).toEqual([
        "preferences",
        "doctor",
        "logs",
      ]);
      expect(search.action).toBe("search");
      expect(
        search.events.some((event: { command: string }) => event.command === "preferences"),
      ).toBe(true);
      expect(summary.action).toBe("summary");
      expect(summary.byCommand.preferences).toBeGreaterThanOrEqual(1);
      expect(summary.byCommand.doctor).toBeGreaterThanOrEqual(1);
      expect(technicalSearch.action).toBe("search");
      expect(
        technicalSearch.events.some(
          (event: { category: string; event: string }) =>
            event.category === "technical" && event.event === "command.started",
        ),
      ).toBe(true);
      expect(allSummary.byCategory.usage).toBeGreaterThanOrEqual(1);
      expect(allSummary.byCategory.technical).toBeGreaterThanOrEqual(1);
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  }, 30_000);
});
