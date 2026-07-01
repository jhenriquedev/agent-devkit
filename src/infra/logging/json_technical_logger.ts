import { homedir } from "node:os";
import { join } from "node:path";
import type { AgentDataStore } from "../bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { TechnicalLogEvent, TechnicalLogger, TechnicalLogInput } from "../bases/logger";
import { Result } from "../bases/result";
import { LocalAgentDataStore } from "../data";
import { redactRecord } from "../helpers/redaction";

export type JsonTechnicalLoggerOptions = {
  clock?: () => Date;
  dataStore?: AgentDataStore;
  retentionDays?: number;
  stateDirectory?: string;
};

function defaultStateDirectory(): string {
  return join(homedir(), ".agent-devkit");
}

function logFileName(timestamp: Date): string {
  return `technical-${timestamp.toISOString().slice(0, 10)}.jsonl`;
}

function cutoffDate(timestamp: Date, retentionDays: number): string {
  const cutoff = new Date(
    Date.UTC(timestamp.getUTCFullYear(), timestamp.getUTCMonth(), timestamp.getUTCDate()),
  );
  cutoff.setUTCDate(cutoff.getUTCDate() - retentionDays);
  return cutoff.toISOString().slice(0, 10);
}

function dateFromLogFile(fileName: string): string | undefined {
  return /^technical-\d{4}-\d{2}-\d{2}\.jsonl$/.test(fileName)
    ? fileName.replace(/^technical-/, "").replace(/\.jsonl$/, "")
    : undefined;
}

function normalizeMetadata(
  metadata?: Record<string, unknown>,
): Record<string, unknown> | undefined {
  if (metadata === undefined) {
    return undefined;
  }

  const normalized = Object.fromEntries(
    Object.entries(metadata).filter(
      ([, value]) => value !== undefined && typeof value !== "function",
    ),
  );

  return Object.keys(normalized).length > 0 ? redactRecord(normalized) : undefined;
}

export class JsonTechnicalLogger implements TechnicalLogger {
  readonly #clock: () => Date;
  readonly #dataStore: AgentDataStore;
  readonly #retentionDays: number;

  constructor(options: JsonTechnicalLoggerOptions = {}) {
    this.#clock = options.clock ?? (() => new Date());
    this.#dataStore =
      options.dataStore ??
      new LocalAgentDataStore({
        rootDirectory: join(options.stateDirectory ?? defaultStateDirectory(), "data"),
      });
    this.#retentionDays = options.retentionDays ?? 30;
  }

  async writeTechnical(input: TechnicalLogInput): Promise<Result<AgentDevKitErrorCode, void>> {
    const timestamp = this.#clock();
    const { createStateIfMissing, ...logInput } = input;
    const event: TechnicalLogEvent = {
      ...logInput,
      category: "technical",
      metadata: normalizeMetadata(input.metadata),
      schema: "agent-devkit.technical-log/v1",
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
