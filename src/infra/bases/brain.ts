import { z } from "zod";
import type { AgentDevKitErrorCode } from "./errors";
import { AgentPromptSchema } from "./prompt";
import type { Result } from "./result";

export const BrainGenerationOptionsSchema = z
  .object({
    maxInputTokens: z.number().int().positive().optional(),
    maxOutputTokens: z.number().int().positive().optional(),
    model: z.string().min(1).optional(),
    provider: z.enum(["mock"]).default("mock"),
    seed: z.number().int().optional(),
    stop: z.array(z.string().min(1)).optional(),
    stream: z.boolean().optional(),
    temperature: z.number().min(0).max(2).optional(),
    topK: z.number().int().positive().optional(),
    topP: z.number().min(0).max(1).optional(),
  })
  .strict();

export const BrainRequestSchema = z
  .object({
    options: BrainGenerationOptionsSchema.default({ provider: "mock" }),
    prompt: AgentPromptSchema,
    schema: z.literal("agent-devkit.brain-request/v1"),
  })
  .strict();

export const BrainResponseSchema = z
  .object({
    finishReason: z.enum(["error", "length", "stop", "tool-call"]).optional(),
    model: z.string().min(1).optional(),
    provider: z.string().min(1).optional(),
    schema: z.literal("agent-devkit.brain-response/v1"),
    text: z.string(),
    usage: z
      .object({
        inputTokens: z.number().int().nonnegative().optional(),
        outputTokens: z.number().int().nonnegative().optional(),
        totalTokens: z.number().int().nonnegative().optional(),
      })
      .strict()
      .optional(),
  })
  .strict();

export type BrainGenerationOptions = z.infer<typeof BrainGenerationOptionsSchema>;
export type BrainRequest = z.infer<typeof BrainRequestSchema>;
export type BrainResponse = z.infer<typeof BrainResponseSchema>;

export interface BrainProviderPort {
  generate(request: BrainRequest): Promise<Result<AgentDevKitErrorCode, BrainResponse>>;
}
