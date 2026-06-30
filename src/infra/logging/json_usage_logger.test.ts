import { mkdir, mkdtemp, readdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { JsonUsageLogger } from "./json_usage_logger";

describe("json usage logger", () => {
  it("writes categorized usage events as json lines", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-logs-"));
    const now = new Date("2026-06-30T12:00:00.000Z");
    const logger = new JsonUsageLogger({
      clock: () => now,
      stateDirectory: join(root, ".agent-devkit"),
    });

    const result = await logger.writeUsage({
      area: "user",
      argv: ["preferences", "--json"],
      command: "preferences",
      durationMs: 12,
      interface: "cli",
      options: { json: true },
      status: "succeeded",
    });

    expect(result.isOk()).toBe(true);

    const content = await readFile(
      join(root, ".agent-devkit", "logs", "usage-2026-06-30.jsonl"),
      "utf8",
    );
    const event = JSON.parse(content.trim());

    expect(event).toMatchObject({
      area: "user",
      argv: ["preferences", "--json"],
      category: "usage",
      command: "preferences",
      durationMs: 12,
      interface: "cli",
      level: "info",
      options: { json: true },
      schema: "agent-devkit.usage-log/v1",
      status: "succeeded",
      timestamp: "2026-06-30T12:00:00.000Z",
    });
  });

  it("returns a result error when the log directory cannot be written", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-logs-"));
    await writeFile(join(root, ".agent-devkit"), "not a directory");
    const logger = new JsonUsageLogger({
      stateDirectory: join(root, ".agent-devkit"),
    });

    const result = await logger.writeUsage({
      area: "system",
      argv: ["doctor"],
      command: "doctor",
      durationMs: 1,
      interface: "cli",
      options: {},
      status: "succeeded",
    });

    expect(result.isErr()).toBe(true);
  });

  it("removes usage log files older than the configured retention window", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-logs-"));
    const logsDirectory = join(root, ".agent-devkit", "logs");
    const now = new Date("2026-06-30T12:00:00.000Z");
    await mkdir(logsDirectory, { recursive: true });
    await writeFile(join(logsDirectory, "usage-2026-05-30.jsonl"), "{}\n");
    await writeFile(join(logsDirectory, "usage-2026-06-01.jsonl"), "{}\n");

    const logger = new JsonUsageLogger({
      clock: () => now,
      retentionDays: 30,
      stateDirectory: join(root, ".agent-devkit"),
    });

    const result = await logger.writeUsage({
      area: "user",
      argv: ["doctor"],
      command: "doctor",
      durationMs: 1,
      interface: "cli",
      options: {},
      status: "succeeded",
    });

    expect(result.isOk()).toBe(true);
    await expect(readdir(logsDirectory)).resolves.toEqual([
      "usage-2026-06-01.jsonl",
      "usage-2026-06-30.jsonl",
    ]);
  });
});
