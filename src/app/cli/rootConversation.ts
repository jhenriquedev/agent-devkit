import { homedir } from "node:os";
import { createBrainDockProvider } from "../../infra/brain/brain_dock";
import {
  createConversationModuleBindings,
  formatConversationChatText,
} from "../../modules/conversation/conversation.index";

export async function runRootConversation(message: string): Promise<void> {
  const bindings = createConversationModuleBindings({
    brainProvider: createBrainDockProvider({ stateDirectory: `${homedir()}/.agent-devkit` }),
    homeDirectory: homedir(),
  });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  const result = await bindings.unwrap().capabilities.chat.execute({
    action: "send",
    message,
  });

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  console.log(formatConversationChatText(result.unwrap()));
}
