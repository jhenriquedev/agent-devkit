import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { Logger } from "../bases/logger";
import { NullLogger } from "../bases/logger";
import { Result } from "../bases/result";
import { errorCause } from "../helpers/error_cause";

export type HttpClientResponse<T> = {
  body: T;
  status: number;
};

export interface HttpClient {
  getJson<T>(
    url: string,
    headers?: Record<string, string>,
  ): Promise<Result<AgentDevKitErrorCode, HttpClientResponse<T>>>;
}

export type FetchHttpClientOptions = {
  logger?: Logger;
  timeoutMs?: number;
};

const defaultTimeoutMs = 30_000;

export class FetchHttpClient implements HttpClient {
  readonly #logger: Logger;
  readonly #timeoutMs: number;

  constructor(options: FetchHttpClientOptions = {}) {
    this.#logger = options.logger ?? new NullLogger();
    this.#timeoutMs = options.timeoutMs ?? defaultTimeoutMs;
  }

  async getJson<T>(
    url: string,
    headers: Record<string, string> = {},
  ): Promise<Result<AgentDevKitErrorCode, HttpClientResponse<T>>> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.#timeoutMs);

    try {
      const response = await fetch(url, { headers, signal: controller.signal });

      if (!response.ok) {
        this.#logger.write("warn", "HTTP request failed with non-success status.", {
          status: response.status,
          url,
        });
        return Result.fail(ErrorCodes.NetworkRequestFailed);
      }

      const body = (await response.json()) as T;
      return Result.ok({
        body,
        status: response.status,
      });
    } catch (error) {
      this.#logger.write("error", "HTTP request failed.", {
        error: errorCause(error),
        url,
      });
      return Result.fail(ErrorCodes.NetworkRequestFailed);
    } finally {
      clearTimeout(timeout);
    }
  }
}
