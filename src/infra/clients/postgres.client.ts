import type {
  DatabaseRow,
  PostgresQuery,
  PostgresQueryExecutor,
  PostgresReadableClient,
} from "../bases/database";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export class PostgresClient implements PostgresReadableClient {
  readonly #executor: PostgresQueryExecutor;

  constructor(executor: PostgresQueryExecutor) {
    this.#executor = executor;
  }

  async queryRows<TRow extends DatabaseRow>(
    query: PostgresQuery,
  ): Promise<Result<AgentDevKitErrorCode, readonly TRow[]>> {
    try {
      const result = await this.#executor.query<TRow>(query.sql, query.values);
      return Result.ok(result.rows);
    } catch {
      return Result.fail(ErrorCodes.DatabaseReadFailed);
    }
  }
}
