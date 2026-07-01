import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";

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
  timeoutMs?: number;
};

const defaultTimeoutMs = 30_000;

export class FetchHttpClient implements HttpClient {
  readonly #timeoutMs: number;

  constructor(options: FetchHttpClientOptions = {}) {
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
      const body = (await response.json()) as T;
      return Result.ok({
        body,
        status: response.status,
      });
    } catch (error) {
      void error;
      return Result.fail(ErrorCodes.NetworkRequestFailed);
    } finally {
      clearTimeout(timeout);
    }
  }
}
