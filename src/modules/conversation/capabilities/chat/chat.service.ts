import type { BrainProviderPort, BrainRequest, BrainResponse } from "../../../../infra/bases/brain";
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

export class MockBrainProvider implements BrainProviderPort {
  async generate(request: BrainRequest): Promise<Result<AgentDevKitErrorCode, BrainResponse>> {
    const text = `${request.prompt.agent.name}: Entendi. Vou responder no contexto da sessão atual: "${request.prompt.task.userMessage}".`;
    const inputTokens = request.prompt.messages
      .map((message) => message.content.split(/\s+/g).filter(Boolean).length)
      .reduce((total, count) => total + count, 0);
    const outputTokens = text.split(/\s+/g).filter(Boolean).length;

    return Result.ok({
      finishReason: "stop",
      model: request.options.model ?? "mock-chat",
      provider: "mock",
      schema: "agent-devkit.brain-response/v1",
      text,
      usage: {
        inputTokens,
        outputTokens,
        totalTokens: inputTokens + outputTokens,
      },
    });
  }
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
      options: parsed.data.brain ?? { provider: "mock" },
      prompt: prepared.unwrap().prompt,
      schema: "agent-devkit.brain-request/v1",
    };
    const brain = await this.#brainProvider.generate(request);

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
