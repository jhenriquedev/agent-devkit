import type { ConversationChatResult } from "./chat.entities";

export function formatConversationChatText(result: ConversationChatResult): string {
  const agentName = result.prompt.agent.name.trim();
  const reply = result.reply.trim();
  const speakerPrefix = `${agentName}:`;
  const normalizedReply = reply.toLowerCase().startsWith(speakerPrefix.toLowerCase())
    ? reply
    : `${speakerPrefix} ${reply}`;
  const metadata = [`Session: ${result.sessionId}`];

  if (result.projectId !== undefined) {
    metadata.push(`Project: ${result.projectId}`);
  }

  if (result.brain.model !== undefined || result.brain.provider !== undefined) {
    metadata.push(
      `Model: ${[result.brain.provider, result.brain.model].filter(Boolean).join("/")}`,
    );
  }

  if (result.brain.usage !== undefined) {
    const tokens = [
      result.brain.usage.inputTokens === undefined
        ? undefined
        : `input ${result.brain.usage.inputTokens}`,
      result.brain.usage.outputTokens === undefined
        ? undefined
        : `output ${result.brain.usage.outputTokens}`,
      result.brain.usage.totalTokens === undefined
        ? undefined
        : `total ${result.brain.usage.totalTokens}`,
    ].filter(Boolean);

    if (tokens.length > 0) {
      metadata.push(`Tokens: ${tokens.join(", ")}`);
    }
  }

  return [normalizedReply, "", ...metadata].join("\n");
}
