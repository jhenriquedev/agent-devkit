import type { InvokableCapabilityService } from "../infra/bases/capability";
import type { AgentDevKitErrorCode } from "../infra/bases/errors";
import type { AgentDevKitModuleConfig } from "../infra/bases/module";
import type { Result } from "../infra/bases/result";
import type { IModuleSurface } from "../infra/bases/surface";
import { type ContextModuleBindOptions, createContextModuleBindings } from "./context/context.bind";
import { contextModuleConfig } from "./context/context.config";
import { createContextSurface } from "./context/context.surface";
import {
  type ConversationModuleBindOptions,
  createConversationModuleBindings,
} from "./conversation/conversation.bind";
import { conversationModuleConfig } from "./conversation/conversation.config";
import { createConversationSurface } from "./conversation/conversation.surface";
import {
  createEnvironmentModuleBindings,
  type EnvironmentModuleBindOptions,
} from "./environment/environment.bind";
import { environmentModuleConfig } from "./environment/environment.config";
import { createEnvironmentSurface } from "./environment/environment.surface";
import { createLogsModuleBindings, type LogsModuleBindOptions } from "./logs/logs.bind";
import { logsModuleConfig } from "./logs/logs.config";
import { createLogsSurface } from "./logs/logs.surface";
import { createModelsModuleBindings, type ModelsModuleBindOptions } from "./models/models.bind";
import { modelsModuleConfig } from "./models/models.config";
import { createModelsSurface } from "./models/models.surface";
import { createProjectModuleBindings, type ProjectModuleBindOptions } from "./project/project.bind";
import { projectModuleConfig } from "./project/project.config";
import { createProjectSurface } from "./project/project.surface";
import { createSecretsModuleBindings, type SecretsModuleBindOptions } from "./secrets/secrets.bind";
import { secretsModuleConfig } from "./secrets/secrets.config";
import { createSecretsSurface } from "./secrets/secrets.surface";
import { createSelfModuleBindings, type SelfModuleBindOptions } from "./self/self.bind";
import { selfModuleConfig } from "./self/self.config";
import { createSelfSurface } from "./self/self.surface";
import { createUserModuleBindings, type UserModuleBindOptions } from "./user/user.bind";
import { userModuleConfig } from "./user/user.config";
import { createUserSurface } from "./user/user.surface";

export type AgentModuleRegistryOptions = ProjectModuleBindOptions &
  SelfModuleBindOptions & {
    conversation?: ConversationModuleBindOptions;
    context?: ContextModuleBindOptions;
    environment?: EnvironmentModuleBindOptions;
    logs?: LogsModuleBindOptions;
    models?: ModelsModuleBindOptions;
    secrets?: SecretsModuleBindOptions;
    user?: UserModuleBindOptions;
  };

export type AgentModuleBindingView = {
  capabilities: Record<string, InvokableCapabilityService>;
};

export type AgentModuleDefinition = {
  bind: (
    options: AgentModuleRegistryOptions,
  ) => Result<AgentDevKitErrorCode, AgentModuleBindingView>;
  capabilities: (binding: AgentModuleBindingView) => InvokableCapabilityService[];
  config: AgentDevKitModuleConfig;
  id: string;
  surface: () => IModuleSurface;
};

function capabilities(binding: AgentModuleBindingView): InvokableCapabilityService[] {
  return Object.values(binding.capabilities);
}

function bindingView<TBinding extends { capabilities: Record<string, InvokableCapabilityService> }>(
  binding: TBinding,
): AgentModuleBindingView {
  return binding;
}

export const agentModuleDefinitions: AgentModuleDefinition[] = [
  {
    id: "conversation",
    config: conversationModuleConfig,
    surface: createConversationSurface,
    bind: (options) =>
      createConversationModuleBindings(options.conversation ?? {}).map((binding) =>
        bindingView(binding),
      ),
    capabilities,
  },
  {
    id: "context",
    config: contextModuleConfig,
    surface: createContextSurface,
    bind: (options) =>
      createContextModuleBindings(options.context ?? {}).map((binding) => bindingView(binding)),
    capabilities,
  },
  {
    id: "environment",
    config: environmentModuleConfig,
    surface: createEnvironmentSurface,
    bind: (options) =>
      createEnvironmentModuleBindings(options.environment ?? {}).map((binding) =>
        bindingView(binding),
      ),
    capabilities,
  },
  {
    id: "logs",
    config: logsModuleConfig,
    surface: createLogsSurface,
    bind: (options) =>
      createLogsModuleBindings(options.logs ?? {}).map((binding) => bindingView(binding)),
    capabilities,
  },
  {
    id: "models",
    config: modelsModuleConfig,
    surface: createModelsSurface,
    bind: (options) =>
      createModelsModuleBindings(options.models ?? {}).map((binding) => bindingView(binding)),
    capabilities,
  },
  {
    id: "project",
    config: projectModuleConfig,
    surface: createProjectSurface,
    bind: (options) =>
      createProjectModuleBindings({ appVersion: options.appVersion }).map((binding) =>
        bindingView(binding),
      ),
    capabilities,
  },
  {
    id: "secrets",
    config: secretsModuleConfig,
    surface: createSecretsSurface,
    bind: (options) =>
      createSecretsModuleBindings(options.secrets ?? {}).map((binding) => bindingView(binding)),
    capabilities,
  },
  {
    id: "self",
    config: selfModuleConfig,
    surface: createSelfSurface,
    bind: (options) =>
      createSelfModuleBindings({
        currentVersion: options.currentVersion,
        packageName: options.packageName,
      }).map((binding) => bindingView(binding)),
    capabilities,
  },
  {
    id: "user",
    config: userModuleConfig,
    surface: createUserSurface,
    bind: (options) =>
      createUserModuleBindings(options.user ?? {}).map((binding) => bindingView(binding)),
    capabilities,
  },
];
