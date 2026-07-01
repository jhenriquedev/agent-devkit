import type {
  CapabilityInvocationInterface,
  CapabilityRepositoryPort,
} from "../../../../infra/bases/capability";
import type { CharacterDefinition, CharacterId } from "../../../../infra/bases/character";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import type { AgentPrompt, PromptMessage } from "../../../../infra/bases/prompt";
import { AgentPromptSchema } from "../../../../infra/bases/prompt";
import { Result } from "../../../../infra/bases/result";
import type { ContextProject } from "../../../context/capabilities/projects/projects.entities";
import type { ContextProjectsRepositoryPort } from "../../../context/capabilities/projects/projects.repository";
import type {
  ContextMessage,
  ContextSession,
  ContextSessionOrigin,
} from "../../../context/capabilities/sessions/sessions.entities";
import type { ContextSessionsRepositoryPort } from "../../../context/capabilities/sessions/sessions.repository";
import type { PersonalizationRepositoryPort } from "../../../user/capabilities/personalization/personalization.repository";
import type { ConversationChatOptions } from "./chat.entities";

export type ConversationPromptPreparation = {
  messages: ContextMessage[];
  prompt: AgentPrompt;
  projectId?: string;
  sessionId: string;
};

export type ConversationChatRepositoryOptions = {
  clock?: () => Date;
  personalizationRepository: PersonalizationRepositoryPort;
  projectsRepository: ContextProjectsRepositoryPort;
  sessionsRepository: ContextSessionsRepositoryPort;
};

export interface ConversationChatRepositoryPort extends CapabilityRepositoryPort {
  appendAssistantMessage(
    sessionId: string,
    content: string,
  ): Promise<Result<AgentDevKitErrorCode, ContextMessage[]>>;
  preparePrompt(
    input: ConversationChatOptions,
    origin: CapabilityInvocationInterface,
  ): Promise<Result<AgentDevKitErrorCode, ConversationPromptPreparation>>;
}

function originFromInterface(origin: CapabilityInvocationInterface): ContextSessionOrigin {
  return origin;
}

function promptMessages(messages: ContextMessage[]): PromptMessage[] {
  return messages.map((message) => ({
    content: message.content,
    createdAt: message.createdAt,
    id: message.id,
    role: message.role === "tool" ? "tool" : message.role,
  }));
}

function characterName(character: CharacterDefinition): string {
  return character.name ?? character.id;
}

function compact(value: string): string {
  return value.replaceAll(/\s+/g, " ").trim();
}

export class ConversationChatRepository implements ConversationChatRepositoryPort {
  readonly repositoryId = "conversation.chat.repository";
  readonly #clock: () => Date;
  readonly #personalizationRepository: PersonalizationRepositoryPort;
  readonly #projectsRepository: ContextProjectsRepositoryPort;
  readonly #sessionsRepository: ContextSessionsRepositoryPort;

  constructor(options: ConversationChatRepositoryOptions) {
    this.#clock = options.clock ?? (() => new Date());
    this.#personalizationRepository = options.personalizationRepository;
    this.#projectsRepository = options.projectsRepository;
    this.#sessionsRepository = options.sessionsRepository;
  }

  async appendAssistantMessage(
    sessionId: string,
    content: string,
  ): Promise<Result<AgentDevKitErrorCode, ContextMessage[]>> {
    const append = await this.#sessionsRepository.appendMessage({
      content,
      role: "assistant",
      sessionId,
    });

    if (append.isErr()) {
      return Result.fail(append.unwrapError());
    }

    const details = await this.#sessionsRepository.show({
      includeMessages: true,
      sessionId,
    });

    if (details.isErr()) {
      return Result.fail(details.unwrapError());
    }

    return Result.ok(details.unwrap().messages ?? []);
  }

  async preparePrompt(
    input: ConversationChatOptions,
    origin: CapabilityInvocationInterface,
  ): Promise<Result<AgentDevKitErrorCode, ConversationPromptPreparation>> {
    if (input.action !== "send") {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const character = await this.#loadCharacter(input.characterId);

    if (character.isErr()) {
      return Result.fail(character.unwrapError());
    }

    const project = await this.#loadProject(input.projectId);

    if (project.isErr()) {
      return Result.fail(project.unwrapError());
    }

    const session = await this.#ensureSession(input, originFromInterface(origin));

    if (session.isErr()) {
      return Result.fail(session.unwrapError());
    }

    const append = await this.#sessionsRepository.appendMessage({
      content: input.message,
      role: "user",
      sessionId: session.unwrap().id,
    });

    if (append.isErr()) {
      return Result.fail(append.unwrapError());
    }

    const details = await this.#sessionsRepository.show({
      includeMessages: true,
      sessionId: session.unwrap().id,
    });

    if (details.isErr()) {
      return Result.fail(details.unwrapError());
    }

    const loadedProject =
      project.unwrap() ??
      (details.unwrap().session.projectId === undefined
        ? undefined
        : await this.#loadProject(details.unwrap().session.projectId).then((result) =>
            result.isOk() ? result.unwrap() : undefined,
          ));
    const allMessages = details.unwrap().messages ?? [];
    const messagesForPrompt = input.includeHistory === false ? allMessages.slice(-1) : allMessages;
    const prompt = this.#prompt({
      character: character.unwrap(),
      messages: messagesForPrompt,
      project: loadedProject,
      session: details.unwrap().session,
      userMessage: input.message,
    });

    if (prompt.isErr()) {
      return Result.fail(prompt.unwrapError());
    }

    return Result.ok({
      messages: allMessages,
      projectId: loadedProject?.id,
      prompt: prompt.unwrap(),
      sessionId: details.unwrap().session.id,
    });
  }

  async #ensureSession(
    input: Extract<ConversationChatOptions, { action: "send" }>,
    origin: ContextSessionOrigin,
  ): Promise<Result<AgentDevKitErrorCode, ContextSession>> {
    if (input.sessionId !== undefined) {
      const details = await this.#sessionsRepository.show({
        includeMessages: false,
        sessionId: input.sessionId,
      });

      if (details.isErr()) {
        return Result.fail(details.unwrapError());
      }

      if (input.projectId !== undefined && details.unwrap().session.projectId !== input.projectId) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      return Result.ok(details.unwrap().session);
    }

    const created = await this.#sessionsRepository.create({
      origin,
      projectId: input.projectId,
      title: compact(input.message).slice(0, 80) || "Untitled chat",
    });

    return created.isOk() ? Result.ok(created.unwrap()) : Result.fail(created.unwrapError());
  }

  async #loadCharacter(
    characterId?: CharacterId,
  ): Promise<Result<AgentDevKitErrorCode, CharacterDefinition>> {
    const profile = await this.#personalizationRepository.loadProfile();

    if (profile.isErr()) {
      return Result.fail(profile.unwrapError());
    }

    if (characterId === undefined || characterId === profile.unwrap().currentCharacter.id) {
      return Result.ok(profile.unwrap().currentCharacter);
    }

    const characters = await this.#personalizationRepository.loadCharacters(characterId);

    if (characters.isErr()) {
      return Result.fail(characters.unwrapError());
    }

    const character = characters.unwrap().find((candidate) => candidate.id === characterId);

    if (character === undefined || !character.active) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const { custom, selected, spritePath, ...definition } = character;
    void custom;
    void selected;
    void spritePath;

    return Result.ok(definition);
  }

  async #loadProject(
    projectId?: string,
  ): Promise<Result<AgentDevKitErrorCode, ContextProject | undefined>> {
    if (projectId === undefined) {
      return Result.ok(undefined);
    }

    const project = await this.#projectsRepository.show(projectId);

    return project.isOk() ? Result.ok(project.unwrap()) : Result.fail(project.unwrapError());
  }

  #prompt(input: {
    character: CharacterDefinition;
    messages: ContextMessage[];
    project?: ContextProject;
    session: ContextSession;
    userMessage: string;
  }): Result<AgentDevKitErrorCode, AgentPrompt> {
    const prompt = AgentPromptSchema.safeParse({
      agent: {
        behavior: input.character.profile.behavior,
        characterId: input.character.id,
        detailLevel: input.character.profile.detailLevel,
        name: characterName(input.character),
        tone: input.character.profile.tone,
        traits: input.character.profile.traits,
      },
      context: {
        knowledge: [],
        project:
          input.project === undefined
            ? undefined
            : {
                description: input.project.description,
                id: input.project.id,
                name: input.project.name,
                path: input.project.path,
                tags: input.project.tags,
              },
        session: {
          id: input.session.id,
          messageCount: input.messages.length,
          title: input.session.title,
        },
      },
      locale: "pt-BR",
      messages: promptMessages(input.messages),
      output: { format: "text", language: "pt-BR" },
      policies: {
        allowToolCalls: false,
        approvalRequired: false,
        maxToolCalls: 0,
      },
      schema: "agent-devkit.prompt/v1",
      task: {
        userMessage: input.userMessage,
      },
      tools: [],
    });

    return prompt.success ? Result.ok(prompt.data) : Result.fail(ErrorCodes.InvalidInput);
  }
}
