import type {
  DatabaseRow,
  PostgresQuery,
  PostgresQueryExecutor,
  PostgresReadableClient,
} from "../bases/database";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { Logger } from "../bases/logger";
import { NullLogger } from "../bases/logger";
import { Result } from "../bases/result";
import { errorCause } from "../helpers/error_cause";

export type PostgresClientOptions = {
  logger?: Logger;
  timeoutMs?: number;
};

const defaultTimeoutMs = 30_000;

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("Postgres query timed out.")), timeoutMs);

    promise.then(
      (value) => {
        clearTimeout(timeout);
        resolve(value);
      },
      (error: unknown) => {
        clearTimeout(timeout);
        reject(error);
      },
    );
  });
}

export class PostgresClient implements PostgresReadableClient {
  readonly #executor: PostgresQueryExecutor;
  readonly #logger: Logger;
  readonly #timeoutMs: number;

  constructor(executor: PostgresQueryExecutor, options: PostgresClientOptions = {}) {
    this.#executor = executor;
    this.#logger = options.logger ?? new NullLogger();
    this.#timeoutMs = options.timeoutMs ?? defaultTimeoutMs;
  }

  async queryRows<TRow extends DatabaseRow>(
    query: PostgresQuery,
  ): Promise<Result<AgentDevKitErrorCode, readonly TRow[]>> {
    try {
      const result = await withTimeout(
        this.#executor.query<TRow>(query.sql, query.values),
        this.#timeoutMs,
      );
      return Result.ok(result.rows);
    } catch (error) {
      this.#logger.write("error", "Postgres query failed.", {
        error: errorCause(error),
        sql: query.sql,
      });
      return Result.fail(ErrorCodes.DatabaseReadFailed);
    }
  }
}
