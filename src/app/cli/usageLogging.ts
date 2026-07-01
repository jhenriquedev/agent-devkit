import type {
  LogLevel,
  TechnicalLogger,
  UsageLogArea,
  UsageLogger,
} from "../../infra/bases/logger";
import { errorCause } from "../../infra/helpers/error_cause";
import { redactArgv, redactRecord } from "../../infra/helpers/redaction";

type CliUsageLoggingMiddlewareOptions = {
  argv?: string[];
  clock?: () => number;
  logger: UsageLogger;
  technicalLogger?: TechnicalLogger;
};

type CliUsageMetadata = {
  area: UsageLogArea;
  command: string;
  createStateIfMissing?: boolean;
  options?: () => Record<string, unknown>;
  redactOptions?: string[];
};

export class CliUsageLoggingMiddleware {
  readonly #argv: string[];
  readonly #clock: () => number;
  readonly #logger: UsageLogger;
  readonly #technicalLogger?: TechnicalLogger;

  constructor(options: CliUsageLoggingMiddlewareOptions) {
    this.#argv = options.argv ?? process.argv.slice(2);
    this.#clock = options.clock ?? (() => Date.now());
    this.#logger = options.logger;
    this.#technicalLogger = options.technicalLogger;
  }

  track<TArgs extends unknown[]>(
    metadata: CliUsageMetadata,
    handler: (...args: TArgs) => Promise<void> | void,
  ): (...args: TArgs) => Promise<void> {
    return async (...args: TArgs) => {
      const startedAt = this.#clock();

      try {
        await this.#writeTechnical(metadata, "command.started", "info", "CLI command started");
        await handler(...args);
        await this.#writeTechnical(
          metadata,
          "command.succeeded",
          "info",
          "CLI command succeeded",
          this.#clock() - startedAt,
        );
        await this.#write(metadata, "succeeded", this.#clock() - startedAt);
      } catch (error) {
        await this.#writeTechnical(
          metadata,
          "command.failed",
          "error",
          "CLI command failed",
          this.#clock() - startedAt,
          error,
        );
        await this.#write(metadata, "failed", this.#clock() - startedAt, error);
        throw error;
      }
    };
  }

  async #write(
    metadata: CliUsageMetadata,
    status: "failed" | "succeeded",
    durationMs: number,
    error?: unknown,
  ): Promise<void> {
    await this.#logger.writeUsage({
      area: metadata.area,
      argv: redactArgv(this.#argv, metadata.redactOptions),
      command: metadata.command,
      createStateIfMissing: metadata.createStateIfMissing,
      durationMs: Math.max(0, durationMs),
      error: error === undefined ? undefined : errorCause(error),
      interface: "cli",
      options: redactRecord(metadata.options?.() ?? {}, metadata.redactOptions),
      status,
    });
  }

  async #writeTechnical(
    metadata: CliUsageMetadata,
    event: string,
    level: LogLevel,
    message: string,
    durationMs?: number,
    error?: unknown,
  ): Promise<void> {
    if (this.#technicalLogger === undefined) {
      return;
    }

    await this.#technicalLogger.writeTechnical({
      area: metadata.area,
      command: metadata.command,
      createStateIfMissing: metadata.createStateIfMissing,
      durationMs: durationMs === undefined ? undefined : Math.max(0, durationMs),
      error: error === undefined ? undefined : errorCause(error),
      event,
      interface: "cli",
      level,
      message,
      metadata: {
        argv: redactArgv(this.#argv, metadata.redactOptions),
        options: redactRecord(metadata.options?.() ?? {}, metadata.redactOptions),
      },
    });
  }
}
