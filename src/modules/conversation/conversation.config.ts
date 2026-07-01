import { defineModuleConfig } from "../../infra/bases/module";
import { conversationChatCapabilityConfig } from "./capabilities/chat/chat.service";

export const conversationModuleConfig = defineModuleConfig({
  id: "conversation",
  name: "Conversation",
  description: "Agent DevKit chat runtime backed by personalization, projects and sessions.",
  capabilities: [conversationChatCapabilityConfig.id],
  tests: {
    include: [
      "src/modules/conversation/conversation.surface.test.ts",
      "src/modules/conversation/capabilities/**/*.test.ts",
    ],
  },
} as const);
