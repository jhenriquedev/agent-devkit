import type { RedisKeyValueExecutor, RedisReadableClient } from "../bases/database";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { Logger } from "../bases/logger";
import { NullLogger } from "../bases/logger";
import { Result } from "../bases/result";
import { errorCause } from "../helpers/error_cause";

export type RedisClientOptions = {
  logger?: Logger;
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
  readonly #logger: Logger;
  readonly #timeoutMs: number;

  constructor(executor: RedisKeyValueExecutor, options: RedisClientOptions = {}) {
    this.#executor = executor;
    this.#logger = options.logger ?? new NullLogger();
    this.#timeoutMs = options.timeoutMs ?? defaultTimeoutMs;
  }

  async getHash(key: string): Promise<Result<AgentDevKitErrorCode, Record<string, string>>> {
    try {
      return Result.ok(await withTimeout(this.#executor.hGetAll(key), this.#timeoutMs));
    } catch (error) {
      this.#logger.write("error", "Redis hash read failed.", {
        error: errorCause(error),
        key,
      });
      return Result.fail(ErrorCodes.CacheReadFailed);
    }
  }

  async getString(key: string): Promise<Result<AgentDevKitErrorCode, string | null>> {
    try {
      return Result.ok(await withTimeout(this.#executor.get(key), this.#timeoutMs));
    } catch (error) {
      this.#logger.write("error", "Redis string read failed.", {
        error: errorCause(error),
        key,
      });
      return Result.fail(ErrorCodes.CacheReadFailed);
    }
  }
}
