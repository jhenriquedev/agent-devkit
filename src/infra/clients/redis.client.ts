import type { RedisKeyValueExecutor, RedisReadableClient } from "../bases/database";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export type RedisClientOptions = {
  timeoutMs?: number;
};

const defaultTimeoutMs = 30_000;

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("Redis operation timed out.")), timeoutMs);

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

export class RedisClient implements RedisReadableClient {
  readonly #executor: RedisKeyValueExecutor;
  readonly #timeoutMs: number;

  constructor(executor: RedisKeyValueExecutor, options: RedisClientOptions = {}) {
    this.#executor = executor;
    this.#timeoutMs = options.timeoutMs ?? defaultTimeoutMs;
  }

  async getHash(key: string): Promise<Result<AgentDevKitErrorCode, Record<string, string>>> {
    try {
      return Result.ok(await withTimeout(this.#executor.hGetAll(key), this.#timeoutMs));
    } catch (error) {
      void error;
      return Result.fail(ErrorCodes.CacheReadFailed);
    }
  }

  async getString(key: string): Promise<Result<AgentDevKitErrorCode, string | null>> {
    try {
      return Result.ok(await withTimeout(this.#executor.get(key), this.#timeoutMs));
    } catch (error) {
      void error;
      return Result.fail(ErrorCodes.CacheReadFailed);
    }
  }
}
