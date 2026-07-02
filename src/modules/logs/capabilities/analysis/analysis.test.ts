import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { LogsAnalysisRepository } from "./analysis.repository";
import { LogsAnalysisService } from "./analysis.service";

async function writeUsageLog(
  homeDirectory: string,
  date: string,
  events: Array<Record<string, unknown>>,
): Promise<void> {
  const logsDirectory = join(homeDirectory, ".agent-devkit", "data", "logs");
  await mkdir(logsDirectory, { recursive: true });
  await writeFile(
    join(logsDirectory, `usage-${date}.jsonl`),
    `${events.map((event) => JSON.stringify(event)).join("\n")}\n`,
  );
}

async function writeTechnicalLog(
  homeDirectory: string,
  date: string,
  events: Array<Record<string, unknown>>,
): Promise<void> {
  const logsDirectory = join(homeDirectory, ".agent-devkit", "data", "logs");
  await mkdir(logsDirectory, { recursive: true });
  await writeFile(
    join(logsDirectory, `technical-${date}.jsonl`),
    `${events.map((event) => JSON.stringify(event)).join("\n")}\n`,
  );
}

function event(overrides: Record<string, unknown>) {
  return {
    area: "user",
    argv: ["preferences", "--json"],
    category: "usage",
    command: "preferences",
    durationMs: 10,
    interface: "cli",
    level: "info",
    options: { json: true },
    schema: "agent-devkit.usage-log/v1",
    status: "succeeded",
    timestamp: "2026-06-30T12:00:00.000Z",
    ...overrides,
  };
}

function technicalEvent(overrides: Record<string, unknown>) {
  return {
    area: "system",
    category: "technical",
    command: "secrets.set",
    durationMs: 20,
    event: "command.succeeded",
    interface: "cli",
    level: "info",
    message: "CLI command succeeded",
    metadata: { options: { json: true } },
    schema: "agent-devkit.technical-log/v1",
    timestamp: "2026-06-30T12:00:00.000Z",
    ...overrides,
  };
}

describe("logs.analysis", () => {
  it("lists available usage log files with event counts", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-module-"));

    try {
      await writeUsageLog(home, "2026-06-29", [event({ command: "doctor" })]);
      await writeUsageLog(home, "2026-06-30", [
        event({ command: "preferences" }),
        event({ command: "reset" }),
      ]);
      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const result = await service.execute({ action: "list" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "list",
        files: [
          { date: "2026-06-30", eventCount: 2 },
          { date: "2026-06-29", eventCount: 1 },
        ],
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("keeps legacy log files readable when canonical logs do not exist", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-module-"));

    try {
      const legacyLogsDirectory = join(home, ".agent-devkit", "logs");
      await mkdir(legacyLogsDirectory, { recursive: true });
      await writeFile(
        join(legacyLogsDirectory, "usage-2026-06-30.jsonl"),
        `${JSON.stringify(event({ command: "legacy.doctor" }))}\n`,
      );

      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const result = await service.execute({ action: "list" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "list",
        files: [{ date: "2026-06-30", eventCount: 1, file: "usage-2026-06-30.jsonl" }],
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("reads and tails usage events by date", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-module-"));

    try {
      await writeUsageLog(home, "2026-06-30", [
        event({ command: "doctor", timestamp: "2026-06-30T12:00:00.000Z" }),
        event({ command: "preferences", timestamp: "2026-06-30T12:01:00.000Z" }),
        event({ command: "reset", timestamp: "2026-06-30T12:02:00.000Z" }),
      ]);
      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const result = await service.execute({
        action: "read",
        date: "2026-06-30",
        limit: 2,
        tail: true,
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "read",
        events: [{ command: "preferences" }, { command: "reset" }],
        totalEvents: 3,
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("returns no tail events when limit is zero", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-module-"));

    try {
      await writeUsageLog(home, "2026-06-30", [
        event({ command: "doctor", timestamp: "2026-06-30T12:00:00.000Z" }),
        event({ command: "preferences", timestamp: "2026-06-30T12:01:00.000Z" }),
      ]);
      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const result = await service.execute({
        action: "read",
        limit: 0,
        tail: true,
      });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "read",
        events: [],
        totalEvents: 2,
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("searches usage events across command, area, status and argv", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-module-"));

    try {
      await writeUsageLog(home, "2026-06-30", [
        event({ command: "doctor", area: "project", argv: ["doctor"] }),
        event({ command: "preferences", area: "user", argv: ["preferences", "themes"] }),
      ]);
      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const result = await service.execute({ action: "search", query: "themes" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "search",
        query: "themes",
        events: [{ command: "preferences" }],
        totalMatches: 1,
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("summarizes usage by command, area and status", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-logs-module-"));

    try {
      await writeUsageLog(home, "2026-06-30", [
        event({ command: "doctor", area: "project", durationMs: 20 }),
        event({ command: "doctor", area: "project", status: "failed", durationMs: 40 }),
        event({ command: "preferences", area: "user", durationMs: 30 }),
      ]);
      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const result = await service.execute({ action: "summary" });

      expect(result.isOk()).toBe(true);
      expect(result.unwrap()).toMatchObject({
        action: "summary",
        averageDurationMs: 30,
        byArea: { project: 2, user: 1 },
        byCategory: { usage: 3 },
        byCommand: { doctor: 2, preferences: 1 },
        byStatus: { failed: 1, succeeded: 2 },
        totalEvents: 3,
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });

  it("lists, searches and summarizes technical logs", async () => {
    const home = await mkdtemp(join(tmpdir(), "agent-devkit-technical-logs-module-"));

    try {
      await writeUsageLog(home, "2026-06-30", [event({ command: "preferences" })]);
      await writeTechnicalLog(home, "2026-06-30", [
        technicalEvent({ command: "secrets.set", event: "command.succeeded" }),
        technicalEvent({
          command: "secrets.show",
          event: "command.failed",
          level: "error",
          message: "CLI command failed",
        }),
      ]);
      const service = new LogsAnalysisService({
        repository: new LogsAnalysisRepository({ homeDirectory: home }),
      });

      const list = await service.execute({ action: "list", category: "all" });
      const search = await service.execute({
        action: "search",
        category: "technical",
        query: "command.failed",
      });
      const summary = await service.execute({ action: "summary", category: "all" });

      expect(list.isOk()).toBe(true);
      expect(list.unwrap()).toMatchObject({
        files: [
          expect.objectContaining({ category: "technical", eventCount: 2 }),
          expect.objectContaining({ category: "usage", eventCount: 1 }),
        ],
      });
      expect(search.isOk()).toBe(true);
      expect(search.unwrap()).toMatchObject({
        action: "search",
        events: [expect.objectContaining({ category: "technical", event: "command.failed" })],
        totalMatches: 1,
      });
      expect(summary.isOk()).toBe(true);
      expect(summary.unwrap()).toMatchObject({
        byCategory: { technical: 2, usage: 1 },
        byCommand: { preferences: 1, "secrets.set": 1, "secrets.show": 1 },
        byStatus: { error: 1, info: 1, succeeded: 1 },
      });
    } finally {
      await rm(home, { force: true, recursive: true });
    }
  });
});
