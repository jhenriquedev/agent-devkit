import { BaseCapabilityService, defineCapabilityConfig } from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type LogCategorySelection,
  type LogEvent,
  type LogsAnalysisOptions,
  LogsAnalysisOptionsSchema,
  type LogsAnalysisResult,
  LogsAnalysisResultSchema,
} from "./analysis.entities";
import type { LogsAnalysisRepositoryPort } from "./analysis.repository";

type LogsAnalysisServiceDependencies = {
  repository: LogsAnalysisRepositoryPort;
};

export const logsAnalysisCapabilityConfig = defineCapabilityConfig({
  id: "logs.analysis",
  moduleId: "logs",
  name: "Logs Analysis",
  description: "Inspect, search and summarize Agent DevKit usage logs.",
  kind: "deterministic",
  risk: "read-only",
} as const);

function countBy(
  events: LogEvent[],
  selector: (event: LogEvent) => string,
): Record<string, number> {
  return events.reduce<Record<string, number>>((accumulator, event) => {
    const key = selector(event);
    accumulator[key] = (accumulator[key] ?? 0) + 1;
    return accumulator;
  }, {});
}

function limitEvents(events: LogEvent[], limit = 20): LogEvent[] {
  return events.slice(0, Math.max(0, limit));
}

function tailEvents(events: LogEvent[], limit = 20): LogEvent[] {
  const normalizedLimit = Math.max(0, limit);
  return normalizedLimit === 0 ? [] : events.slice(-normalizedLimit);
}

function commandName(event: LogEvent): string {
  return event.category === "usage" ? event.command : (event.command ?? event.event);
}

function durationMs(event: LogEvent): number {
  return event.durationMs ?? 0;
}

function statusName(event: LogEvent): string {
  return event.category === "usage" ? event.status : event.level;
}

function searchableText(event: LogEvent): string {
  return [
    event.area,
    commandName(event),
    statusName(event),
    event.timestamp,
    event.interface,
    event.category === "usage" ? event.argv.join(" ") : undefined,
    event.category === "usage" ? JSON.stringify(event.options) : JSON.stringify(event.metadata),
    event.category === "technical" ? event.event : undefined,
    event.category === "technical" ? event.message : undefined,
    event.error?.message,
    event.error?.name,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export class LogsAnalysisService extends BaseCapabilityService<
  typeof logsAnalysisCapabilityConfig,
  LogsAnalysisServiceDependencies
> {
  readonly inputSchema = LogsAnalysisOptionsSchema;
  readonly outputSchema = LogsAnalysisResultSchema;
  readonly #repository: LogsAnalysisRepositoryPort;

  constructor(dependencies: LogsAnalysisServiceDependencies) {
    super(logsAnalysisCapabilityConfig, dependencies);
    this.#repository = dependencies.repository;
  }

  async execute(
    options: LogsAnalysisOptions,
  ): Promise<Result<AgentDevKitErrorCode, LogsAnalysisResult>> {
    if (options.action === "list") {
      const files = await this.#repository.listFiles(options.category);
      return files.isOk()
        ? Result.ok({ action: "list", files: files.unwrap(), path: this.#repository.logsPath() })
        : Result.fail(files.unwrapError());
    }

    const category: LogCategorySelection =
      "category" in options ? (options.category ?? "usage") : "usage";
    const events = await this.#repository.readEvents(
      "date" in options ? options.date : undefined,
      category,
    );

    if (events.isErr()) {
      return Result.fail(events.unwrapError());
    }

    const allEvents = events.unwrap();

    if (options.action === "read") {
      const selected =
        options.tail === true
          ? tailEvents(allEvents, options.limit)
          : limitEvents(allEvents, options.limit);
      return Result.ok({
        action: "read",
        events: selected,
        path: this.#repository.logsPath(),
        totalEvents: allEvents.length,
      });
    }

    if (options.action === "search") {
      const query = options.query.trim().toLowerCase();

      if (query.length === 0) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      const matches = allEvents.filter((event) => searchableText(event).includes(query));
      return Result.ok({
        action: "search",
        events: limitEvents(matches, options.limit),
        path: this.#repository.logsPath(),
        query: options.query,
        totalMatches: matches.length,
      });
    }

    const totalDurationMs = allEvents.reduce((total, event) => total + durationMs(event), 0);

    return Result.ok({
      action: "summary",
      averageDurationMs:
        allEvents.length === 0 ? 0 : Math.round(totalDurationMs / allEvents.length),
      byArea: countBy(allEvents, (event) => event.area),
      byCategory: countBy(allEvents, (event) => event.category),
      byCommand: countBy(allEvents, commandName),
      byStatus: countBy(allEvents, statusName),
      path: this.#repository.logsPath(),
      slowest: [...allEvents]
        .sort((left, right) => durationMs(right) - durationMs(left))
        .slice(0, 5),
      totalEvents: allEvents.length,
    });
  }

  invoke(options: LogsAnalysisOptions): Promise<Result<AgentDevKitErrorCode, LogsAnalysisResult>> {
    return this.execute(options);
  }
}
