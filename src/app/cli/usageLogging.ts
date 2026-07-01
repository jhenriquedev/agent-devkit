import type {
  LogLevel,
  TechnicalLogger,
  UsageLogArea,
  UsageLogger,
} from "../../infra/bases/logger";

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

function serializeError(error: unknown): { message: string; name: string } {
  if (error instanceof Error) {
    return {
      message: error.message,
      name: error.name,
    };
  }

  return {
    message: String(error),
    name: "Error",
  };
}

function redactArgv(argv: string[], redactOptions: string[] = []): string[] {
  const sensitive = new Set(redactOptions);
  const redacted: string[] = [];

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];

    if (token === undefined) {
      continue;
    }

    if (sensitive.has(token)) {
      redacted.push(token);
      if (index + 1 < argv.length) {
        redacted.push("[redacted]");
        index += 1;
      }
      continue;
    }

    const [flag] = token.split("=");
    if (flag !== undefined && sensitive.has(flag) && token.includes("=")) {
      redacted.push(`${flag}=[redacted]`);
      continue;
    }

    redacted.push(token);
  }

  return redacted;
}

function redactOptions(
  options: Record<string, unknown>,
  redactOptionNames: string[] = [],
): Record<string, unknown> {
  const names = new Set(
    redactOptionNames.map((option) =>
      option.replace(/^--?/, "").replace(/-([a-z])/g, (_, char) => char.toUpperCase()),
    ),
  );

  return Object.fromEntries(
    Object.entries(options).map(([key, value]) => [key, names.has(key) ? "[redacted]" : value]),
  );
}

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
      error: error === undefined ? undefined : serializeError(error),
      interface: "cli",
      options: redactOptions(metadata.options?.() ?? {}, metadata.redactOptions),
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
      error: error === undefined ? undefined : serializeError(error),
      event,
      interface: "cli",
      level,
      message,
      metadata: {
        argv: redactArgv(this.#argv, metadata.redactOptions),
        options: redactOptions(metadata.options?.() ?? {}, metadata.redactOptions),
      },
    });
  }
}
