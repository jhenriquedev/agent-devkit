import type {
  BrainProviderPort,
  BrainRequest,
  BrainResponse,
  BrainStreamHandler,
} from "../../../../infra/bases/brain";
import {
  BaseCapabilityService,
  type CapabilityApproval,
  type CapabilityEffect,
  type CapabilityInvocationContext,
  defineCapabilityConfig,
} from "../../../../infra/bases/capability";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import {
  type ConversationChatOptions,
  ConversationChatOptionsSchema,
  type ConversationChatResult,
  ConversationChatResultSchema,
} from "./chat.entities";
import type { ConversationChatRepositoryPort } from "./chat.repository";

type ConversationChatServiceDependencies = {
  brainProvider: BrainProviderPort;
  repository: ConversationChatRepositoryPort;
};

export const conversationChatCapabilityConfig = defineCapabilityConfig({
  id: "conversation.chat",
  moduleId: "conversation",
  name: "Conversation chat",
  description: "Send a chat message using local personalization, projects and session memory.",
  kind: "brain-assisted",
  risk: "writes-global-state",
} as const);

export { MockBrainProvider } from "../../../../infra/brain/mock_provider";

function normalizeQuestion(value: string): string {
  return value
    .normalize("NFD")
    .replaceAll(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replaceAll(/[^\p{Letter}\p{Number}\s]/gu, " ")
    .replaceAll(/\s+/g, " ")
    .trim();
}

function isSelfDescriptionQuestion(message: string): boolean {
  const normalized = normalizeQuestion(message);

  return (
    normalized === "o que voce pode fazer" ||
    normalized === "o que voce faz" ||
    normalized === "quais sao suas capacidades" ||
    normalized === "quais suas capacidades" ||
    normalized === "what can you do" ||
    normalized === "what do you do"
  );
}

function countPromptTokens(request: BrainRequest): number {
  return request.prompt.messages
    .map((message) => message.content.split(/\s+/g).filter(Boolean).length)
    .reduce((total, count) => total + count, 0);
}

function selfDescriptionResponse(request: BrainRequest): BrainResponse | undefined {
  if (!isSelfDescriptionQuestion(request.prompt.task.userMessage)) {
    return undefined;
  }

  const { agent } = request.prompt;
  const traits =
    agent.traits.length === 0 ? "sem tracos extras configurados" : agent.traits.join(", ");
  const text = `${agent.name}: Eu posso conversar com voce mantendo o contexto da sessao, ajudar a raciocinar, organizar ideias, analisar informacoes e responder no meu estilo configurado. Minha postura e ${agent.behavior}, meu tom e ${agent.tone}, meu nivel de detalhe e ${agent.detailLevel}, e meus tracos atuais sao: ${traits}.`;
  const inputTokens = countPromptTokens(request);
  const outputTokens = text.split(/\s+/g).filter(Boolean).length;

  return {
    finishReason: "stop",
    model: "self-description",
    provider: "system",
    schema: "agent-devkit.brain-response/v1",
    text,
    usage: {
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
    },
  };
}

export class ConversationChatService extends BaseCapabilityService<
  typeof conversationChatCapabilityConfig,
  ConversationChatServiceDependencies,
  ConversationChatOptions,
  ConversationChatResult
> {
  readonly inputSchema = ConversationChatOptionsSchema;
  readonly outputSchema = ConversationChatResultSchema;
  readonly #brainProvider: BrainProviderPort;
  readonly #repository: ConversationChatRepositoryPort;

  constructor(dependencies: ConversationChatServiceDependencies) {
    super(conversationChatCapabilityConfig, dependencies);
    this.#brainProvider = dependencies.brainProvider;
    this.#repository = dependencies.repository;
  }

  async execute(
    options: ConversationChatOptions,
  ): Promise<Result<AgentDevKitErrorCode, ConversationChatResult>> {
    return this.#run(options, { interface: "cli" });
  }

  invoke(
    input: ConversationChatOptions,
    context: CapabilityInvocationContext,
  ): Promise<Result<AgentDevKitErrorCode, ConversationChatResult>> {
    return this.#run(input, context);
  }

  /**
   * Interactive streaming variant used by the CLI/TUI. Emits reply tokens via
   * `onToken` while still resolving to the same `ConversationChatResult` and
   * persisting session memory. MCP and `agent run` use the buffered `execute`.
   */
  stream(
    input: ConversationChatOptions,
    onToken: BrainStreamHandler,
  ): Promise<Result<AgentDevKitErrorCode, ConversationChatResult>> {
    return this.#run(input, { interface: "cli" }, onToken);
  }

  override effectsForInput(): CapabilityEffect[] {
    return [{ operation: "write", scope: "global" }];
  }

  override approvalForInput(): CapabilityApproval {
    return {
      reason: "Conversation chat writes local session memory without tool calls.",
      required: false,
    };
  }

  async #run(
    options: ConversationChatOptions,
    context: Pick<CapabilityInvocationContext, "interface">,
    onToken?: BrainStreamHandler,
  ): Promise<Result<AgentDevKitErrorCode, ConversationChatResult>> {
    const parsed = this.inputSchema.safeParse(options);

    if (!parsed.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const prepared = await this.#repository.preparePrompt(parsed.data, context.interface);

    if (prepared.isErr()) {
      return Result.fail(prepared.unwrapError());
    }

    const request: BrainRequest = {
      options: parsed.data.brain ?? { provider: "local" },
      prompt: prepared.unwrap().prompt,
      schema: "agent-devkit.brain-request/v1",
    };
    const selfDescription = selfDescriptionResponse(request);
    const brain: Result<AgentDevKitErrorCode, BrainResponse> =
      selfDescription === undefined
        ? onToken !== undefined && this.#brainProvider.generateStream !== undefined
          ? await this.#brainProvider.generateStream(request, onToken)
          : await this.#brainProvider.generate(request)
        : Result.ok(selfDescription);

    if (selfDescription !== undefined) {
      onToken?.(selfDescription.text);
    }

    if (brain.isErr()) {
      return Result.fail(brain.unwrapError());
    }

    const messages = await this.#repository.appendAssistantMessage(
      prepared.unwrap().sessionId,
      brain.unwrap().text,
    );

    if (messages.isErr()) {
      return Result.fail(messages.unwrapError());
    }

    const result = this.outputSchema.safeParse({
      action: "send",
      brain: brain.unwrap(),
      messages: messages.unwrap(),
      projectId: prepared.unwrap().projectId,
      prompt: prepared.unwrap().prompt,
      reply: brain.unwrap().text,
      sessionId: prepared.unwrap().sessionId,
    });

    return result.success ? Result.ok(result.data) : Result.fail(ErrorCodes.InvalidInput);
  }
}
