import type { RedisKeyValueExecutor, RedisReadableClient } from "../bases/database";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

export class RedisClient implements RedisReadableClient {
  readonly #executor: RedisKeyValueExecutor;

  constructor(executor: RedisKeyValueExecutor) {
    this.#executor = executor;
  }

  async getHash(key: string): Promise<Result<AgentDevKitErrorCode, Record<string, string>>> {
    try {
      return Result.ok(await this.#executor.hGetAll(key));
    } catch {
      return Result.fail(ErrorCodes.CacheReadFailed);
    }
  }

  async getString(key: string): Promise<Result<AgentDevKitErrorCode, string | null>> {
    try {
      return Result.ok(await this.#executor.get(key));
    } catch {
      return Result.fail(ErrorCodes.CacheReadFailed);
    }
  }
}
