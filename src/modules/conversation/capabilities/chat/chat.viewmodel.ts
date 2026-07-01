import type { ConversationChatResult } from "./chat.entities";

export function formatConversationChatText(result: ConversationChatResult): string {
  const lines = ["Agent:", result.reply, "", `Session: ${result.sessionId}`];

  if (result.projectId !== undefined) {
    lines.push(`Project: ${result.projectId}`);
  }

  return lines.join("\n");
}
