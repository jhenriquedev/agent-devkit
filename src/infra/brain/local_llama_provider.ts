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

function shouldSuppressNodeLlamaLog(line: string): boolean {
  return line.startsWith("[node-llama-cpp]");
}

const defaultLocalGenerationOptions = {
  maxTokens: 512,
  temperature: 0.25,
  topK: 40,
  topP: 0.9,
} as const;

async function suppressNodeLlamaLogs<T>(operation: () => Promise<T>): Promise<T> {
  const originalWrite = process.stderr.write;
  let pending = "";
  const filteredWrite = ((
    chunk: string | Uint8Array,
    encodingOrCallback?: BufferEncoding | ((error?: Error | null) => void),
    callback?: (error?: Error | null) => void,
  ): boolean => {
    const encoding = typeof encodingOrCallback === "string" ? encodingOrCallback : "utf8";
    const done = typeof encodingOrCallback === "function" ? encodingOrCallback : callback;
    const text =
      typeof chunk === "string"
        ? chunk
        : Buffer.isBuffer(chunk)
          ? chunk.toString(encoding)
          : String(chunk);
    const lines = `${pending}${text}`.split(/\r?\n/);
    pending = lines.pop() ?? "";

    for (const line of lines) {
      if (!shouldSuppressNodeLlamaLog(line)) {
        originalWrite.call(process.stderr, `${line}\n`);
      }
    }

    done?.();
    return true;
  }) as typeof process.stderr.write;

  process.stderr.write = filteredWrite;

  try {
    return await operation();
  } finally {
    if (pending.length > 0 && !shouldSuppressNodeLlamaLog(pending)) {
      originalWrite.call(process.stderr, pending);
    }

    process.stderr.write = originalWrite;
  }
}

async function loadNodeLlama(): Promise<Result<AgentDevKitErrorCode, NodeLlamaCpp>> {
  try {
    return Result.ok((await import(nodeLlamaModuleName)) as NodeLlamaCpp);
  } catch {
    return Result.fail(ErrorCodes.BrainProviderUnavailable);
  }
}

export function systemPromptFrom(prompt: AgentPrompt): string {
  const { agent } = prompt;
  const lines = [
    `You are ${agent.name}, the user's configured Agent DevKit personality.`,
    "You operate inside Agent DevKit, a local AI agent toolkit exposed through the `agent` CLI, TUI and MCP.",
    "Answer as the agent. Do not answer as the user, as a generic person, or as a generic chatbot.",
    `Behavior: ${agent.behavior}. Tone: ${agent.tone}. Detail level: ${agent.detailLevel}.`,
    "If the user asks personal questions about you, your personality or what you can do, answer from your configured persona and conversation abilities. Do not list generic human activities. Do not describe Agent DevKit internals unless the user explicitly asks about Agent DevKit, tools, commands, MCP, modules or project capabilities.",
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

  const { session } = prompt.context;

  if (session !== undefined) {
    lines.push(
      `Session: ${session.id}. Title: ${session.title}. Messages: ${session.messageCount}.`,
    );
  }

  if (prompt.context.knowledge.length > 0) {
    lines.push(
      "",
      "Agent DevKit knowledge:",
      ...prompt.context.knowledge.map((knowledge) => `- ${knowledge.content}`),
    );
  }

  if (prompt.tools.length > 0) {
    lines.push(
      "",
      "Available tools:",
      ...prompt.tools.map((tool) => `- ${tool.id} (${tool.risk}): ${tool.description}`),
    );
  }

  lines.push(
    "",
    "Tool policy:",
    `- Tool calls allowed: ${prompt.policies.allowToolCalls ? "yes" : "no"}.`,
    `- Approval required: ${prompt.policies.approvalRequired ? "yes" : "no"}.`,
    `- Max tool calls: ${prompt.policies.maxToolCalls}.`,
  );

  if (!prompt.policies.allowToolCalls) {
    lines.push(
      "- In this mode, do not claim that you already executed actions. If the user asks for a concrete action, explain that direct tool execution is unavailable in this chat turn.",
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
      return await suppressNodeLlamaLogs(async () => {
        const llama = nodeLlama.unwrap();
        const loadedModel = await this.#loadModel(llama, model.unwrap().path);
        const context = await loadedModel.createContext();
        const session = new llama.LlamaChatSession({
          contextSequence: context.getSequence(),
          systemPrompt: systemPromptFrom(request.prompt),
        });

        const text = await session.prompt(request.prompt.task.userMessage, {
          grammar: await this.#grammarFor(options.jsonSchema),
          maxTokens: request.options.maxOutputTokens ?? defaultLocalGenerationOptions.maxTokens,
          onTextChunk: options.onToken,
          seed: request.options.seed,
          temperature: request.options.temperature ?? defaultLocalGenerationOptions.temperature,
          topK: request.options.topK ?? defaultLocalGenerationOptions.topK,
          topP: request.options.topP ?? defaultLocalGenerationOptions.topP,
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
