import { defineModuleBinding, ModuleBinder, type ModuleBinding } from "../../infra/bases/bind";
import type { BrainProviderPort } from "../../infra/bases/brain";
import type { AgentDataStore } from "../../infra/bases/data_store";
import type { AgentDevKitErrorCode } from "../../infra/bases/errors";
import type { Result } from "../../infra/bases/result";
import { LocalAgentDataStore } from "../../infra/data";
import { ContextProjectsRepository } from "../context/capabilities/projects/projects.repository";
import { ContextSessionsRepository } from "../context/capabilities/sessions/sessions.repository";
import { PersonalizationRepository } from "../user/capabilities/personalization/personalization.repository";
import {
  ConversationChatRepository,
  type ConversationChatRepositoryPort,
} from "./capabilities/chat/chat.repository";
import { ConversationChatService, MockBrainProvider } from "./capabilities/chat/chat.service";
import { conversationModuleConfig } from "./conversation.config";

export type ConversationModuleBindOptions = {
  brainProvider?: BrainProviderPort;
  dataStore?: AgentDataStore;
  homeDirectory?: string;
};

export type ConversationModuleCapabilities = {
  chat: ConversationChatService;
};

export type ConversationModuleBinding = ModuleBinding<
  typeof conversationModuleConfig,
  ConversationModuleCapabilities
>;

type ConversationModuleBinderDependencies = {
  chatRepository: (options: ConversationModuleBindOptions) => ConversationChatRepositoryPort;
};

function normalizeOptions(options: ConversationModuleBindOptions): ConversationModuleBindOptions {
  if (options.dataStore !== undefined || options.homeDirectory === undefined) {
    return options;
  }

  return {
    ...options,
    dataStore: new LocalAgentDataStore({
      rootDirectory: `${options.homeDirectory}/.agent-devkit/data`,
    }),
  };
}

const defaultDependencies: ConversationModuleBinderDependencies = {
  chatRepository: (options) => {
    const normalized = normalizeOptions(options);
    const dataStore = normalized.dataStore;

    return new ConversationChatRepository({
      personalizationRepository: new PersonalizationRepository({
        dataStore,
        homeDirectory: normalized.homeDirectory,
      }),
      projectsRepository: new ContextProjectsRepository({ dataStore }),
      sessionsRepository: new ContextSessionsRepository({ dataStore }),
    });
  },
};

export class ConversationModuleBinder extends ModuleBinder<
  ConversationModuleBindOptions,
  typeof conversationModuleConfig,
  ConversationModuleCapabilities
> {
  readonly #dependencies: ConversationModuleBinderDependencies;

  constructor(dependencies: ConversationModuleBinderDependencies = defaultDependencies) {
    super();
    this.#dependencies = dependencies;
  }

  override bind(
    options: ConversationModuleBindOptions = {},
  ): Result<AgentDevKitErrorCode, ConversationModuleBinding> {
    return defineModuleBinding({
      config: conversationModuleConfig,
      capabilities: {
        chat: new ConversationChatService({
          brainProvider: options.brainProvider ?? new MockBrainProvider(),
          repository: this.#dependencies.chatRepository(options),
        }),
      },
    });
  }
}

export function createConversationModuleBindings(
  options: ConversationModuleBindOptions = {},
): Result<AgentDevKitErrorCode, ConversationModuleBinding> {
  return new ConversationModuleBinder().bind(options);
}
