import type {
  BrainProviderPort,
  BrainRequest,
  BrainResponse,
  BrainStreamHandler,
  BrainStructuredResponse,
} from "../bases/brain";
import { type AgentDevKitErrorCode, ErrorCodes } from "../bases/errors";
import type { AgentPrompt } from "../bases/prompt";
import { Result } from "../bases/result";
import { ModelStore } from "../models/model_store";

// Minimal structural view of the parts of `node-llama-cpp` we depend on. The
// package is an optional native dependency resolved at runtime, so we describe
// only the surface we use instead of importing its types.
type LlamaContextSequence = unknown;

type LlamaChatSession = {
  prompt(
    text: string,
    options?: {
      grammar?: unknown;
      maxTokens?: number;
      onTextChunk?: (chunk: string) => void;
      seed?: number;
      temperature?: number;
      topK?: number;
      topP?: number;
    },
  ): Promise<string>;
};

type LlamaContext = { getSequence(): LlamaContextSequence };
type LlamaModel = { createContext(): Promise<LlamaContext> };
type Llama = {
  createGrammarForJsonSchema?(schema: Record<string, unknown>): Promise<unknown>;
  loadModel(options: { modelPath: string }): Promise<LlamaModel>;
};

type NodeLlamaCpp = {
  getLlama(): Promise<Llama>;
  LlamaChatSession: new (options: {
    contextSequence: LlamaContextSequence;
    systemPrompt?: string;
  }) => LlamaChatSession;
};

// Widened to `string` so TypeScript does not try to resolve the optional
// dependency at build time; it is loaded lazily at runtime.
const nodeLlamaModuleName: string = "node-llama-cpp";

async function loadNodeLlama(): Promise<Result<AgentDevKitErrorCode, NodeLlamaCpp>> {
  try {
    return Result.ok((await import(nodeLlamaModuleName)) as NodeLlamaCpp);
  } catch {
    return Result.fail(ErrorCodes.BrainProviderUnavailable);
  }
}

function systemPromptFrom(prompt: AgentPrompt): string {
  const { agent } = prompt;
  const lines = [
    `You are ${agent.name}.`,
    `Behavior: ${agent.behavior}. Tone: ${agent.tone}. Detail level: ${agent.detailLevel}.`,
  ];

  if (agent.traits.length > 0) {
    lines.push(`Traits: ${agent.traits.join(", ")}.`);
  }

  const { project } = prompt.context;

  if (project !== undefined) {
    lines.push(
      `Project: ${project.name}${project.description === undefined ? "" : ` — ${project.description}`}.`,
    );
  }

  lines.push(`Reply in ${prompt.output.language}.`);

  const history = prompt.messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .slice(0, -1)
    .map((message) => `${message.role === "user" ? "User" : agent.name}: ${message.content}`);

  if (history.length > 0) {
    lines.push("", "Conversation so far:", ...history);
  }

  return lines.join("\n");
}

function extractJson(text: string): unknown {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");

  if (start === -1 || end === -1 || end <= start) {
    return undefined;
  }

  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch {
    return undefined;
  }
}

export type LocalLlamaBrainProviderOptions = {
  store?: ModelStore;
  stateDirectory?: string;
};

export class LocalLlamaBrainProvider implements BrainProviderPort {
  readonly #store: ModelStore;
  readonly #models = new Map<string, LlamaModel>();
  #llama?: Llama;
  #nodeLlama?: NodeLlamaCpp;

  constructor(options: LocalLlamaBrainProviderOptions = {}) {
    this.#store = options.store ?? new ModelStore({ stateDirectory: options.stateDirectory });
  }

  generate(request: BrainRequest): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    return this.#run(request);
  }

  generateStream(
    request: BrainRequest,
    onToken: BrainStreamHandler,
  ): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    return this.#run(request, { onToken });
  }

  async generateStructured(
    request: BrainRequest,
    jsonSchema: Record<string, unknown>,
  ): Promise<Result<AgentDevKitErrorCode, BrainStructuredResponse>> {
    const generated = await this.#run(request, { jsonSchema });

    if (generated.isErr()) {
      return Result.fail(generated.unwrapError());
    }

    const raw = generated.unwrap().text;
    let json: unknown;

    try {
      json = JSON.parse(raw);
    } catch {
      json = extractJson(raw);
    }

    return Result.ok({ json, raw });
  }

  async #run(
    request: BrainRequest,
    options: { jsonSchema?: Record<string, unknown>; onToken?: BrainStreamHandler } = {},
  ): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    const model = await this.#resolveModelPath(request.options.model, request.options.role);

    if (model.isErr()) {
      return Result.fail(model.unwrapError());
    }

    const nodeLlama = await this.#ensureNodeLlama();

    if (nodeLlama.isErr()) {
      return Result.fail(nodeLlama.unwrapError());
    }

    try {
      const llama = nodeLlama.unwrap();
      const loadedModel = await this.#loadModel(llama, model.unwrap().path);
      const context = await loadedModel.createContext();
      const session = new llama.LlamaChatSession({
        contextSequence: context.getSequence(),
        systemPrompt: systemPromptFrom(request.prompt),
      });

      const text = await session.prompt(request.prompt.task.userMessage, {
        grammar: await this.#grammarFor(options.jsonSchema),
        maxTokens: request.options.maxOutputTokens,
        onTextChunk: options.onToken,
        seed: request.options.seed,
        temperature: request.options.temperature,
        topK: request.options.topK,
        topP: request.options.topP,
      });

      const outputTokens = text.split(/\s+/g).filter(Boolean).length;

      return Result.ok({
        finishReason: "stop",
        model: model.unwrap().id,
        provider: "local",
        schema: "agent-devkit.brain-response/v1",
        text,
        usage: { outputTokens },
      });
    } catch {
      return Result.fail(ErrorCodes.BrainProviderUnavailable);
    }
  }

  // Best-effort JSON-schema grammar for constrained decoding. Falls back to
  // free-form output (and prompt-based JSON extraction) if the installed
  // node-llama-cpp version does not expose grammar creation.
  async #grammarFor(jsonSchema?: Record<string, unknown>): Promise<unknown> {
    if (jsonSchema === undefined || this.#llama?.createGrammarForJsonSchema === undefined) {
      return undefined;
    }

    try {
      return await this.#llama.createGrammarForJsonSchema(jsonSchema);
    } catch {
      return undefined;
    }
  }

  async #resolveModelPath(
    requestedModel: string | undefined,
    role: string | undefined,
  ): Promise<Result<AgentDevKitErrorCode, { id: string; path: string }>> {
    let modelId = requestedModel;

    if (modelId === undefined) {
      const defaultId = await this.#store.getDefault(role);
      modelId = defaultId.isOk() ? defaultId.unwrap() : undefined;
    }

    if (modelId === undefined) {
      return Result.fail(ErrorCodes.ModelNotFound);
    }

    const status = await this.#store.status(modelId);

    if (status.isErr()) {
      return Result.fail(status.unwrapError());
    }

    const installed = status.unwrap();

    if (installed === undefined) {
      return Result.fail(ErrorCodes.ModelNotFound);
    }

    return Result.ok({ id: modelId, path: installed.path });
  }

  async #ensureNodeLlama(): Promise<Result<AgentDevKitErrorCode, NodeLlamaCpp>> {
    if (this.#nodeLlama !== undefined) {
      return Result.ok(this.#nodeLlama);
    }

    const loaded = await loadNodeLlama();

    if (loaded.isOk()) {
      this.#nodeLlama = loaded.unwrap();
    }

    return loaded;
  }

  async #loadModel(llama: NodeLlamaCpp, modelPath: string): Promise<LlamaModel> {
    const cached = this.#models.get(modelPath);

    if (cached !== undefined) {
      return cached;
    }

    if (this.#llama === undefined) {
      this.#llama = await llama.getLlama();
    }

    const model = await this.#llama.loadModel({ modelPath });
    this.#models.set(modelPath, model);
    return model;
  }
}
