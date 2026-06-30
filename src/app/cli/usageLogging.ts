import type { UsageLogArea, UsageLogger } from "../../infra/bases/logger";

type CliUsageLoggingMiddlewareOptions = {
  argv?: string[];
  clock?: () => number;
  logger: UsageLogger;
};

type CliUsageMetadata = {
  area: UsageLogArea;
  command: string;
  options?: () => Record<string, unknown>;
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

export class CliUsageLoggingMiddleware {
  readonly #argv: string[];
  readonly #clock: () => number;
  readonly #logger: UsageLogger;

  constructor(options: CliUsageLoggingMiddlewareOptions) {
    this.#argv = options.argv ?? process.argv.slice(2);
    this.#clock = options.clock ?? (() => Date.now());
    this.#logger = options.logger;
  }

  track<TArgs extends unknown[]>(
    metadata: CliUsageMetadata,
    handler: (...args: TArgs) => Promise<void> | void,
  ): (...args: TArgs) => Promise<void> {
    return async (...args: TArgs) => {
      const startedAt = this.#clock();

      try {
        await handler(...args);
        await this.#write(metadata, "succeeded", this.#clock() - startedAt);
      } catch (error) {
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
      argv: this.#argv,
      command: metadata.command,
      durationMs: Math.max(0, durationMs),
      error: error === undefined ? undefined : serializeError(error),
      interface: "cli",
      options: metadata.options?.() ?? {},
      status,
    });
  }
}
