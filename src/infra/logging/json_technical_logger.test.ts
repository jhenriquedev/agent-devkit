import { mkdir, mkdtemp, readdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { JsonTechnicalLogger } from "./json_technical_logger";

describe("json technical logger", () => {
  it("writes technical audit events as json lines", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-technical-logs-"));
    const now = new Date("2026-06-30T12:00:00.000Z");
    const logger = new JsonTechnicalLogger({
      clock: () => now,
      stateDirectory: join(root, ".agent-devkit"),
    });

    const result = await logger.writeTechnical({
      area: "user",
      command: "preferences",
      event: "command.started",
      interface: "cli",
      level: "info",
      message: "CLI command started",
      metadata: { argv: ["preferences", "--json"], options: { json: true } },
    });

    expect(result.isOk()).toBe(true);

    const content = await readFile(
      join(root, ".agent-devkit", "logs", "technical-2026-06-30.jsonl"),
      "utf8",
    );
    const event = JSON.parse(content.trim());

    expect(event).toMatchObject({
      area: "user",
      category: "technical",
      command: "preferences",
      event: "command.started",
      interface: "cli",
      level: "info",
      message: "CLI command started",
      metadata: { argv: ["preferences", "--json"], options: { json: true } },
      schema: "agent-devkit.technical-log/v1",
      timestamp: "2026-06-30T12:00:00.000Z",
    });
  });

  it("removes technical log files older than the configured retention window", async () => {
    const root = await mkdtemp(join(tmpdir(), "agent-devkit-technical-logs-"));
    const logsDirectory = join(root, ".agent-devkit", "logs");
    const now = new Date("2026-06-30T12:00:00.000Z");
    await mkdir(logsDirectory, { recursive: true });
    await writeFile(join(logsDirectory, "technical-2026-05-30.jsonl"), "{}\n");
    await writeFile(join(logsDirectory, "technical-2026-06-01.jsonl"), "{}\n");
    await writeFile(join(logsDirectory, "usage-2026-05-30.jsonl"), "{}\n");

    const logger = new JsonTechnicalLogger({
      clock: () => now,
      retentionDays: 30,
      stateDirectory: join(root, ".agent-devkit"),
    });

    const result = await logger.writeTechnical({
      area: "system",
      command: "doctor",
      event: "command.succeeded",
      interface: "cli",
      level: "info",
      message: "CLI command succeeded",
    });

    expect(result.isOk()).toBe(true);
    await expect(readdir(logsDirectory)).resolves.toEqual([
      "technical-2026-06-01.jsonl",
      "technical-2026-06-30.jsonl",
      "usage-2026-05-30.jsonl",
    ]);
  });
});
