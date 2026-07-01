import { z } from "zod";
import {
  CharacterBehaviorSchema,
  CharacterDetailLevelSchema,
  CharacterIdSchema,
  CharacterToneSchema,
} from "./character";

export const PromptMessageRoleSchema = z.enum(["assistant", "system", "tool", "user"]);

export const PromptMessageSchema = z
  .object({
    content: z.string(),
    createdAt: z.string().datetime().optional(),
    id: z.string().min(1).optional(),
    role: PromptMessageRoleSchema,
  })
  .strict();

export const PromptProjectContextSchema = z
  .object({
    description: z.string().optional(),
    id: z.string().min(1),
    name: z.string().min(1),
    path: z.string().optional(),
    tags: z.array(z.string()).default([]),
  })
  .strict();

export const PromptSessionContextSchema = z
  .object({
    id: z.string().min(1),
    messageCount: z.number().int().nonnegative(),
    title: z.string().min(1),
  })
  .strict();

export const PromptKnowledgeContextSchema = z
  .object({
    content: z.string().min(1),
    id: z.string().min(1),
    source: z.string().min(1).optional(),
  })
  .strict();

export const PromptToolDescriptorSchema = z
  .object({
    description: z.string().min(1),
    id: z.string().min(1),
    inputSchema: z.record(z.string(), z.unknown()).optional(),
    risk: z.string().min(1),
  })
  .strict();

export const PromptOutputContractSchema = z
  .object({
    format: z.enum(["json", "text"]).default("text"),
    language: z.string().min(1).default("pt-BR"),
  })
  .strict();

export const AgentPromptSchema = z
  .object({
    agent: z
      .object({
        behavior: CharacterBehaviorSchema,
        characterId: CharacterIdSchema,
        detailLevel: CharacterDetailLevelSchema,
        name: z.string().min(1),
        tone: CharacterToneSchema,
        traits: z.array(z.string().min(1)).default([]),
      })
      .strict(),
    context: z
      .object({
        knowledge: z.array(PromptKnowledgeContextSchema).default([]),
        project: PromptProjectContextSchema.optional(),
        session: PromptSessionContextSchema.optional(),
      })
      .strict(),
    locale: z.string().min(1).default("pt-BR"),
    messages: z.array(PromptMessageSchema),
    output: PromptOutputContractSchema.default({ format: "text", language: "pt-BR" }),
    policies: z
      .object({
        allowToolCalls: z.boolean(),
        approvalRequired: z.boolean(),
        maxToolCalls: z.number().int().nonnegative(),
      })
      .strict(),
    schema: z.literal("agent-devkit.prompt/v1"),
    task: z
      .object({
        intent: z.string().min(1).optional(),
        userMessage: z.string().min(1),
      })
      .strict(),
    tools: z.array(PromptToolDescriptorSchema).default([]),
  })
  .strict();

export type PromptMessage = z.infer<typeof PromptMessageSchema>;
export type AgentPrompt = z.infer<typeof AgentPromptSchema>;
export type PromptToolDescriptor = z.infer<typeof PromptToolDescriptorSchema>;
