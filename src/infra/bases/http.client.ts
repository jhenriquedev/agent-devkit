import { type AgentDevKitErrorCode, ErrorCodes } from "./errors";
import { Result } from "./result";

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

export class FetchHttpClient implements HttpClient {
  async getJson<T>(
    url: string,
    headers: Record<string, string> = {},
  ): Promise<Result<AgentDevKitErrorCode, HttpClientResponse<T>>> {
    try {
      const response = await fetch(url, { headers });
      const body = (await response.json()) as T;
      return Result.ok({
        body,
        status: response.status,
      });
    } catch {
      return Result.fail(ErrorCodes.NetworkRequestFailed);
    }
  }
}
