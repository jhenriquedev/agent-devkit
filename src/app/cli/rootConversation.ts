import { homedir } from "node:os";
import type { AgentDataPath, AgentDataStore } from "../../infra/bases/data_store";
import { createBrainDockProvider } from "../../infra/brain/brain_dock";
import { LocalAgentDataStore } from "../../infra/data";
import {
  type ContextSessionsService,
  createContextModuleBindings,
} from "../../modules/context/context.index";
import {
  createConversationModuleBindings,
  formatConversationChatText,
} from "../../modules/conversation/conversation.index";

type CliConversationState = {
  activeSessionId: string;
  schema: "agent-devkit.cli-conversation-state/v1";
  updatedAt: string;
};

const cliConversationStatePath = {
  namespace: "conversation",
  segments: ["cli-state.json"],
} satisfies AgentDataPath;

function isCliConversationState(value: unknown): value is CliConversationState {
  const record = value as Partial<CliConversationState>;

  return (
    typeof value === "object" &&
    value !== null &&
    "activeSessionId" in value &&
    "schema" in value &&
    typeof record.activeSessionId === "string" &&
    record.activeSessionId.length > 0 &&
    record.schema === "agent-devkit.cli-conversation-state/v1"
  );
}

async function loadActiveCliSessionId(
  dataStore: AgentDataStore,
  sessions: ContextSessionsService,
): Promise<string | undefined> {
  const state = await dataStore.readJson<unknown>(cliConversationStatePath);

  if (state.isErr()) {
    return undefined;
  }

  const statePayload = state.unwrap();

  if (!isCliConversationState(statePayload)) {
    return undefined;
  }

  const current = await sessions.execute({
    action: "show",
    includeMessages: false,
    sessionId: statePayload.activeSessionId,
  });

  if (current.isErr()) {
    return undefined;
  }

  const result = current.unwrap();

  if (
    result.action !== "show" ||
    result.session.origin !== "cli" ||
    result.session.status !== "active"
  ) {
    return undefined;
  }

  return result.session.id;
}

async function saveActiveCliSessionId(dataStore: AgentDataStore, sessionId: string): Promise<void> {
  await dataStore.writeJson<CliConversationState>(
    cliConversationStatePath,
    {
      activeSessionId: sessionId,
      schema: "agent-devkit.cli-conversation-state/v1",
      updatedAt: new Date().toISOString(),
    },
    { atomic: true },
  );
}

export async function runRootConversation(message: string): Promise<void> {
  const homeDirectory = homedir();
  const dataStore = new LocalAgentDataStore({
    rootDirectory: `${homeDirectory}/.agent-devkit/data`,
  });
  const bindings = createConversationModuleBindings({
    brainProvider: createBrainDockProvider({ stateDirectory: `${homeDirectory}/.agent-devkit` }),
    dataStore,
    homeDirectory,
  });
  const contextBindings = createContextModuleBindings({ dataStore, homeDirectory });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  if (contextBindings.isErr()) {
    throw new Error(contextBindings.unwrapError());
  }

  const activeSessionId = await loadActiveCliSessionId(
    dataStore,
    contextBindings.unwrap().capabilities.sessions,
  );
  const result = await bindings.unwrap().capabilities.chat.execute({
    action: "send",
    message,
    sessionId: activeSessionId,
  });

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload = result.unwrap();
  await saveActiveCliSessionId(dataStore, payload.sessionId);
  console.log(formatConversationChatText(payload));
}
