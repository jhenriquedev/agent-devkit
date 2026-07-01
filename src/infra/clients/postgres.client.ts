import type {
  DatabaseRow,
  PostgresQuery,
  PostgresQueryExecutor,
  PostgresReadableClient,
} from "../bases/database";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export type PostgresClientOptions = {
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
  readonly #timeoutMs: number;

  constructor(executor: PostgresQueryExecutor, options: PostgresClientOptions = {}) {
    this.#executor = executor;
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
      void error;
      return Result.fail(ErrorCodes.DatabaseReadFailed);
    }
  }
}
