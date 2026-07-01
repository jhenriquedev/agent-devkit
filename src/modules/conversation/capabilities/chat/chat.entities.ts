import { z } from "zod";
import { BrainGenerationOptionsSchema, BrainResponseSchema } from "../../../../infra/bases/brain";
import { CharacterIdSchema } from "../../../../infra/bases/character";
import { AgentPromptSchema } from "../../../../infra/bases/prompt";
import { ContextMessageSchema } from "../../../context/capabilities/sessions/sessions.entities";

export const ConversationChatOptionsSchema = z.discriminatedUnion("action", [
  z
    .object({
      action: z.literal("send"),
      brain: BrainGenerationOptionsSchema.optional(),
      characterId: CharacterIdSchema.optional(),
      includeHistory: z.boolean().optional(),
      message: z.string().min(1),
      projectId: z.string().min(1).optional(),
      sessionId: z.string().min(1).optional(),
    })
    .strict(),
]);

export type ConversationChatOptions = z.infer<typeof ConversationChatOptionsSchema>;

export const ConversationChatResultSchema = z
  .object({
    action: z.literal("send"),
    brain: BrainResponseSchema,
    messages: z.array(ContextMessageSchema),
    projectId: z.string().min(1).optional(),
    prompt: AgentPromptSchema,
    reply: z.string(),
    sessionId: z.string().min(1),
  })
  .strict();

export type ConversationChatResult = z.infer<typeof ConversationChatResultSchema>;
