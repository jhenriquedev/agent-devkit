import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type DatabaseRow = Record<string, unknown>;

export type PostgresQuery = {
  readonly sql: string;
  readonly values?: readonly unknown[];
};

export type PostgresQueryResult<TRow extends DatabaseRow> = {
  readonly rows: readonly TRow[];
};

export interface PostgresQueryExecutor {
  query<TRow extends DatabaseRow>(
    sql: string,
    values?: readonly unknown[],
  ): Promise<PostgresQueryResult<TRow>>;
}

export interface PostgresReadableClient {
  queryRows<TRow extends DatabaseRow>(
    query: PostgresQuery,
  ): Promise<Result<AgentDevKitErrorCode, readonly TRow[]>>;
}

export interface RedisKeyValueExecutor {
  get(key: string): Promise<string | null>;
  hGetAll(key: string): Promise<Record<string, string>>;
}

export interface RedisReadableClient {
  getHash(key: string): Promise<Result<AgentDevKitErrorCode, Record<string, string>>>;
  getString(key: string): Promise<Result<AgentDevKitErrorCode, string | null>>;
}
