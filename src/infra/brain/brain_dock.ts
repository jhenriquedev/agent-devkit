import type {
  BrainProviderPort,
  BrainRequest,
  BrainResponse,
  BrainStreamHandler,
  BrainStructuredResponse,
} from "../bases/brain";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import { Result } from "../bases/result";
import { LocalLlamaBrainProvider } from "./local_llama_provider";
import { MockBrainProvider } from "./mock_provider";

export type BrainDockOptions = {
  stateDirectory?: string;
};

type ProviderFactory = () => BrainProviderPort;

const defaultProvider = "local";
const fallbackProvider = "mock";

function shouldFallback(error: AgentDevKitErrorCode): boolean {
  return error === ErrorCodes.BrainProviderUnavailable || error === ErrorCodes.ModelNotFound;
}

/**
 * The "dock": a `BrainProviderPort` that routes each request to a concrete
 * provider by `request.options.provider` (local, mock, and hosted providers
 * later). Streaming is forwarded when the resolved provider supports it, and
 * degrades to a single chunk otherwise.
 */
export class BrainDockProvider implements BrainProviderPort {
  readonly #factories: Map<string, ProviderFactory>;
  readonly #instances = new Map<string, BrainProviderPort>();

  constructor(options: BrainDockOptions = {}) {
    this.#factories = new Map<string, ProviderFactory>([
      ["local", () => new LocalLlamaBrainProvider({ stateDirectory: options.stateDirectory })],
      ["mock", () => new MockBrainProvider()],
    ]);
  }

  async generate(request: BrainRequest): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    const provider = this.#resolve(request);
    const response = await provider.generate(request);

    if (
      response.isOk() ||
      request.options.provider === fallbackProvider ||
      !shouldFallback(response.unwrapError())
    ) {
      return response;
    }

    return this.#resolveById(fallbackProvider).generate({
      ...request,
      options: { ...request.options, provider: fallbackProvider },
    });
  }

  async generateStream(
    request: BrainRequest,
    onToken: BrainStreamHandler,
  ): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    const provider = this.#resolve(request);

    if (provider.generateStream !== undefined) {
      const response = await provider.generateStream(request, onToken);

      if (
        response.isOk() ||
        request.options.provider === fallbackProvider ||
        !shouldFallback(response.unwrapError())
      ) {
        return response;
      }

      return (
        this.#resolveById(fallbackProvider).generateStream?.(
          {
            ...request,
            options: { ...request.options, provider: fallbackProvider },
          },
          onToken,
        ) ??
        this.#resolveById(fallbackProvider).generate({
          ...request,
          options: { ...request.options, provider: fallbackProvider },
        })
      );
    }

    const response = await provider.generate(request);

    if (response.isOk()) {
      onToken(response.unwrap().text);
    }

    return response;
  }

  async generateStructured(
    request: BrainRequest,
    jsonSchema: Record<string, unknown>,
  ): Promise<Result<AgentDevKitErrorCode, BrainStructuredResponse>> {
    const provider = this.#resolve(request);

    if (provider.generateStructured !== undefined) {
      const response = await provider.generateStructured(request, jsonSchema);

      if (
        response.isOk() ||
        request.options.provider === fallbackProvider ||
        !shouldFallback(response.unwrapError())
      ) {
        return response;
      }

      return (
        this.#resolveById(fallbackProvider).generateStructured?.(
          {
            ...request,
            options: { ...request.options, provider: fallbackProvider },
          },
          jsonSchema,
        ) ?? Result.fail(ErrorCodes.BrainProviderUnavailable)
      );
    }

    return Result.fail(ErrorCodes.BrainProviderUnavailable);
  }

  #resolve(request: BrainRequest): BrainProviderPort {
    const id = request.options.provider ?? defaultProvider;
    return this.#resolveById(id);
  }

  #resolveById(id: string): BrainProviderPort {
    const cached = this.#instances.get(id);

    if (cached !== undefined) {
      return cached;
    }

    const factory = this.#factories.get(id) ?? this.#factories.get(defaultProvider);
    const provider = factory === undefined ? new MockBrainProvider() : factory();
    this.#instances.set(id, provider);
    return provider;
  }
}

export function createBrainDockProvider(options: BrainDockOptions = {}): BrainProviderPort {
  return new BrainDockProvider(options);
}
