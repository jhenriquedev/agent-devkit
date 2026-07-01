import { homedir } from "node:os";
import type { Command } from "commander";
import type { Translator } from "../../../infra/bases/i18n";
import {
  type ConversationChatOptions,
  type ConversationChatResult,
  createConversationModuleBindings,
  formatConversationChatText,
} from "../../../modules/conversation/conversation.index";
import { wantsJson } from "../command_options";
import type { CliUsageLoggingMiddleware } from "../usageLogging";

type RegisterChatCommandOptions = {
  translator: Translator;
  usageLogging: CliUsageLoggingMiddleware;
};

type ChatCommandOptions = {
  character?: string;
  json?: boolean;
  noHistory?: boolean;
  project?: string;
  session?: string;
};

function chatCapability() {
  const bindings = createConversationModuleBindings({ homeDirectory: homedir() });

  if (bindings.isErr()) {
    throw new Error(bindings.unwrapError());
  }

  return bindings.unwrap().capabilities.chat;
}

async function printChatResult(
  commandOptions: ChatCommandOptions,
  input: ConversationChatOptions,
): Promise<void> {
  const result = await chatCapability().execute(input);

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload: ConversationChatResult = result.unwrap();

  if (wantsJson(commandOptions)) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(formatConversationChatText(payload));
}

export function registerChatCommand(program: Command, options: RegisterChatCommandOptions): void {
  const chatCommand = program
    .command("chat")
    .alias("ask")
    .argument("<message...>", "message to send")
    .description("send a chat message using Agent DevKit memory and personalization")
    .option("--character <characterId>", "use a character preset for this message")
    .option("--json", "print chat result as JSON")
    .option("--no-history", "build the prompt with only the current message")
    .option("--project <projectId>", "attach a context project")
    .option("--session <sessionId>", "resume a context session");

  chatCommand.action(
    options.usageLogging.track(
      {
        area: "user",
        command: "chat",
        options: () => chatCommand.opts(),
      },
      async (messageParts: string[], commandOptions: ChatCommandOptions) => {
        await printChatResult(commandOptions, {
          action: "send",
          characterId: commandOptions.character,
          includeHistory: commandOptions.noHistory === true ? false : undefined,
          message: messageParts.join(" ").trim(),
          projectId: commandOptions.project,
          sessionId: commandOptions.session,
        });
      },
    ),
  );
}
