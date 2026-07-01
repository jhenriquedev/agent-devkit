import { homedir } from "node:os";
import { join } from "node:path";
import type { AgentDataStore } from "../bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { UsageLogEvent, UsageLogger, UsageLogInput } from "../bases/logger";
import { Result } from "../bases/result";
import { LocalAgentDataStore } from "../data";
import { redactRecord } from "../helpers/redaction";

export type JsonUsageLoggerOptions = {
  clock?: () => Date;
  dataStore?: AgentDataStore;
  retentionDays?: number;
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

function logFileName(timestamp: Date): string {
  return `usage-${timestamp.toISOString().slice(0, 10)}.jsonl`;
}

function cutoffDate(timestamp: Date, retentionDays: number): string {
  const cutoff = new Date(
    Date.UTC(timestamp.getUTCFullYear(), timestamp.getUTCMonth(), timestamp.getUTCDate()),
  );
  cutoff.setUTCDate(cutoff.getUTCDate() - retentionDays);
  return cutoff.toISOString().slice(0, 10);
}

function dateFromLogFile(fileName: string): string | undefined {
  return /^usage-\d{4}-\d{2}-\d{2}\.jsonl$/.test(fileName)
    ? fileName.replace(/^usage-/, "").replace(/\.jsonl$/, "")
    : undefined;
}

function normalizeOptions(options: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(options).filter(
      ([, value]) => value !== undefined && typeof value !== "function",
    ),
  );
}

export class JsonUsageLogger implements UsageLogger {
  readonly #clock: () => Date;
  readonly #dataStore: AgentDataStore;
  readonly #retentionDays: number;

  constructor(options: JsonUsageLoggerOptions = {}) {
    this.#clock = options.clock ?? (() => new Date());
    this.#dataStore =
      options.dataStore ??
      new LocalAgentDataStore({
        rootDirectory: join(options.stateDirectory ?? defaultStateDirectory(), "data"),
      });
    this.#retentionDays = options.retentionDays ?? 30;
  }

  async writeUsage(input: UsageLogInput): Promise<Result<AgentDevKitErrorCode, void>> {
    const timestamp = this.#clock();
    const { createStateIfMissing, ...logInput } = input;
    const event: UsageLogEvent = {
      ...logInput,
      category: "usage",
      level: input.status === "failed" ? "error" : "info",
      options: redactRecord(normalizeOptions(input.options)),
      schema: "agent-devkit.usage-log/v1",
      timestamp: timestamp.toISOString(),
    };

    try {
      if (createStateIfMissing === false) {
        const logsExist = await this.#dataStore.exists({ namespace: "logs", segments: [] });

        if (logsExist.isErr()) {
          return Result.fail(logsExist.unwrapError());
        }

        if (!logsExist.unwrap()) {
          return Result.ok(undefined);
        }
      }

      const write = await this.#dataStore.appendJsonl(
        { namespace: "logs", segments: [logFileName(timestamp)] },
        event,
      );

      if (write.isErr()) {
        return Result.fail(write.unwrapError());
      }

      await this.#cleanupOldLogs(timestamp);
      return Result.ok(undefined);
    } catch {
      return Result.fail(ErrorCodes.FileWriteFailed);
    }
  }

  async #cleanupOldLogs(timestamp: Date): Promise<void> {
    if (!Number.isInteger(this.#retentionDays) || this.#retentionDays < 1) {
      return;
    }

    const cutoff = cutoffDate(timestamp, this.#retentionDays);
    const entries = await this.#dataStore.list({ namespace: "logs", segments: [] });

    if (entries.isErr()) {
      return;
    }

    await Promise.all(
      entries.unwrap().flatMap((entry) => {
        const date = dateFromLogFile(entry.name);
        return date !== undefined && date < cutoff ? [this.#dataStore.remove(entry.path)] : [];
      }),
    );
  }
}
