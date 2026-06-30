import { appendFile, mkdir, readdir, unlink } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { TechnicalLogEvent, TechnicalLogger, TechnicalLogInput } from "../bases/logger";
import { Result } from "../bases/result";

export type JsonTechnicalLoggerOptions = {
  clock?: () => Date;
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

  return Object.keys(normalized).length > 0 ? normalized : undefined;
}

export class JsonTechnicalLogger implements TechnicalLogger {
  readonly #clock: () => Date;
  readonly #retentionDays: number;
  readonly #stateDirectory: string;

  constructor(options: JsonTechnicalLoggerOptions = {}) {
    this.#clock = options.clock ?? (() => new Date());
    this.#retentionDays = options.retentionDays ?? 30;
    this.#stateDirectory = options.stateDirectory ?? defaultStateDirectory();
  }

  async writeTechnical(input: TechnicalLogInput): Promise<Result<AgentDevKitErrorCode, void>> {
    const timestamp = this.#clock();
    const logPath = join(this.#stateDirectory, "logs", logFileName(timestamp));
    const event: TechnicalLogEvent = {
      ...input,
      category: "technical",
      metadata: normalizeMetadata(input.metadata),
      schema: "agent-devkit.technical-log/v1",
      timestamp: timestamp.toISOString(),
    };

    try {
      await mkdir(dirname(logPath), { recursive: true });
      await appendFile(logPath, `${JSON.stringify(event)}\n`, "utf8");
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

    const logsDirectory = join(this.#stateDirectory, "logs");
    const cutoff = cutoffDate(timestamp, this.#retentionDays);
    const files = await readdir(logsDirectory);

    await Promise.all(
      files.flatMap((file) => {
        const date = dateFromLogFile(file);
        return date !== undefined && date < cutoff ? [unlink(join(logsDirectory, file))] : [];
      }),
    );
  }
}
