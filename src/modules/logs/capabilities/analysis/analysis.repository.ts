import { readdir, readFile, stat } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";
import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDataStore } from "../../../../infra/bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { LocalAgentDataStore } from "../../../../infra/data";
import {
  type LogCategory,
  type LogCategorySelection,
  type LogEvent,
  type LogsFileSummary,
  type TechnicalLogRecord,
  TechnicalLogRecordSchema,
  type UsageLogRecord,
  UsageLogRecordSchema,
} from "./analysis.entities";

export type LogsAnalysisRepositoryOptions = {
  dataStore?: AgentDataStore;
  homeDirectory?: string;
  stateDirectory?: string;
};

export interface LogsAnalysisRepositoryPort extends CapabilityRepositoryPort {
  logsPath(): string;
  listFiles(
    category?: LogCategorySelection,
  ): Promise<Result<AgentDevKitErrorCode, LogsFileSummary[]>>;
  readEvents(
    date?: string,
    category?: LogCategorySelection,
  ): Promise<Result<AgentDevKitErrorCode, LogEvent[]>>;
}

type LogFileReference = {
  file: string;
  path: string;
};

function stateDirectory(options: LogsAnalysisRepositoryOptions): string {
  return options.stateDirectory ?? join(options.homeDirectory ?? homedir(), ".agent-devkit");
}

function fileInfo(file: string): { category: LogCategory; date: string } | undefined {
  const usage = /^usage-(\d{4}-\d{2}-\d{2})\.jsonl$/.exec(file);
  if (usage?.[1] !== undefined) {
    return { category: "usage", date: usage[1] };
  }

  const technical = /^technical-(\d{4}-\d{2}-\d{2})\.jsonl$/.exec(file);
  if (technical?.[1] !== undefined) {
    return { category: "technical", date: technical[1] };
  }

  return undefined;
}

function categoryMatches(
  category: LogCategory,
  selection: LogCategorySelection = "usage",
): boolean {
  return selection === "all" || selection === category;
}

function toEvent(
  record: TechnicalLogRecord | UsageLogRecord,
  source: string,
  line: number,
): LogEvent {
  return {
    ...record,
    date: record.timestamp.slice(0, 10),
    line,
    source,
  };
}

function parseEvents(content: string, source: string): LogEvent[] {
  return content
    .split("\n")
    .map((line, index) => ({ index, line: line.trim() }))
    .filter(({ line }) => line.length > 0)
    .flatMap(({ index, line }) => {
      try {
        const payload = JSON.parse(line);
        const parsed =
          payload.category === "technical"
            ? TechnicalLogRecordSchema.safeParse(payload)
            : UsageLogRecordSchema.safeParse(payload);
        return parsed.success ? [toEvent(parsed.data, source, index + 1)] : [];
      } catch {
        return [];
      }
    });
}

export class LogsAnalysisRepository implements LogsAnalysisRepositoryPort {
  readonly repositoryId = "logs.analysis.repository";
  readonly #dataStore: AgentDataStore;
  readonly #legacyLogsDirectory: string;
  readonly #logsDirectory: string;

  constructor(options: LogsAnalysisRepositoryOptions = {}) {
    const state = stateDirectory(options);
    this.#dataStore =
      options.dataStore ?? new LocalAgentDataStore({ rootDirectory: join(state, "data") });
    const resolvedLogsDirectory = this.#dataStore.resolve({ namespace: "logs", segments: [] });
    this.#logsDirectory = resolvedLogsDirectory.isOk()
      ? resolvedLogsDirectory.unwrap()
      : join(state, "data", "logs");
    this.#legacyLogsDirectory = join(state, "logs");
  }

  logsPath(): string {
    return this.#logsDirectory;
  }

  async listFiles(
    category: LogCategorySelection = "usage",
  ): Promise<Result<AgentDevKitErrorCode, LogsFileSummary[]>> {
    const files = await this.#logFiles();

    if (files.isErr()) {
      return Result.fail(files.unwrapError());
    }

    const summaries: LogsFileSummary[] = [];

    try {
      for (const file of files.unwrap()) {
        const info = fileInfo(file.file);

        if (info === undefined || !categoryMatches(info.category, category)) {
          continue;
        }

        const [metadata, content] = await Promise.all([
          stat(file.path),
          readFile(file.path, "utf8"),
        ]);
        summaries.push({
          category: info.category,
          date: info.date,
          eventCount: parseEvents(content, file.file).length,
          file: file.file,
          path: file.path,
          sizeBytes: metadata.size,
        });
      }
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }

    return Result.ok(
      summaries.sort(
        (left, right) =>
          right.date.localeCompare(left.date) || left.category.localeCompare(right.category),
      ),
    );
  }

  async readEvents(
    date?: string,
    category: LogCategorySelection = "usage",
  ): Promise<Result<AgentDevKitErrorCode, LogEvent[]>> {
    const files = await this.#logFiles();

    if (files.isErr()) {
      return Result.fail(files.unwrapError());
    }

    const selectedFiles = files
      .unwrap()
      .filter((file) => {
        const info = fileInfo(file.file);
        return (
          info !== undefined &&
          categoryMatches(info.category, category) &&
          (date === undefined || info.date === date)
        );
      })
      .sort((left, right) => left.file.localeCompare(right.file));
    const events: LogEvent[] = [];

    try {
      for (const file of selectedFiles) {
        events.push(...parseEvents(await readFile(file.path, "utf8"), file.file));
      }
    } catch {
      return Result.fail(ErrorCodes.FileReadFailed);
    }

    return Result.ok(events.sort((left, right) => left.timestamp.localeCompare(right.timestamp)));
  }

  async #logFiles(): Promise<Result<AgentDevKitErrorCode, LogFileReference[]>> {
    try {
      const files = new Map<string, LogFileReference>();

      for (const reference of [
        ...(await this.#readFilesFromDirectory(this.#logsDirectory)),
        ...(await this.#readFilesFromDirectory(this.#legacyLogsDirectory)),
      ]) {
        if (!files.has(reference.file)) {
          files.set(reference.file, reference);
        }
      }

      return Result.ok(
        [...files.values()].sort((left, right) => left.file.localeCompare(right.file)),
      );
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        return Result.ok([]);
      }

      return Result.fail(ErrorCodes.FileReadFailed);
    }
  }

  async #readFilesFromDirectory(directory: string): Promise<LogFileReference[]> {
    try {
      const files = await readdir(directory);
      return files
        .filter((file) => fileInfo(file) !== undefined)
        .map((file) => ({ file, path: join(directory, file) }));
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        return [];
      }

      throw error;
    }
  }
}
