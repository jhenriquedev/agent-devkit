import { z } from "zod";
import type { AgentDevKitErrorCode } from "./errors";
import { AgentPromptSchema } from "./prompt";
import type { Result } from "./result";

export const BrainGenerationOptionsSchema = z
  .object({
    maxInputTokens: z.number().int().positive().optional(),
    maxOutputTokens: z.number().int().positive().optional(),
    model: z.string().min(1).optional(),
    provider: z.enum(["local", "mock"]).default("local"),
    role: z.enum(["agent", "chat"]).optional(),
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
    options: BrainGenerationOptionsSchema.default({ provider: "local" }),
    prompt: AgentPromptSchema,
    schema: z.literal("agent-devkit.brain-request/v1"),
  })
  .strict();

export const BrainToolCallSchema = z
  .object({
    arguments: z.record(z.string(), z.unknown()).default({}),
    id: z.string().min(1).optional(),
    name: z.string().min(1),
  })
  .strict();

export const BrainResponseSchema = z
  .object({
    finishReason: z.enum(["error", "length", "stop", "tool-call"]).optional(),
    model: z.string().min(1).optional(),
    provider: z.string().min(1).optional(),
    schema: z.literal("agent-devkit.brain-response/v1"),
    text: z.string(),
    toolCalls: z.array(BrainToolCallSchema).optional(),
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
export type BrainToolCall = z.infer<typeof BrainToolCallSchema>;

/** Live token callback for streaming-capable providers. */
export type BrainStreamHandler = (delta: string) => void;

/** Result of a JSON-schema-constrained generation used by the agent loop. */
export type BrainStructuredResponse = {
  json: unknown;
  raw: string;
};

export interface BrainProviderPort {
  generate(request: BrainRequest): Promise<Result<AgentDevKitErrorCode, BrainResponse>>;
  /**
   * Optional streaming path. Emits text deltas via `onToken` while still
   * resolving to the complete `BrainResponse` for persistence. Providers that
   * cannot stream simply omit this method; callers fall back to `generate`.
   */
  generateStream?(
    request: BrainRequest,
    onToken: BrainStreamHandler,
  ): Promise<Result<AgentDevKitErrorCode, BrainResponse>>;
  /**
   * Optional structured path for the agent loop: generate output shaped by a
   * JSON schema and return the parsed value plus the raw text. Providers that
   * cannot constrain output omit this method; the agent falls back gracefully.
   */
  generateStructured?(
    request: BrainRequest,
    jsonSchema: Record<string, unknown>,
  ): Promise<Result<AgentDevKitErrorCode, BrainStructuredResponse>>;
}
