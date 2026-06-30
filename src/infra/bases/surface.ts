import { z } from "zod";
import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export const SurfaceCapabilitySchema = z.object({
  id: z.string().min(1),
  kind: z.enum(["brain-assisted", "composite", "deterministic", "external"]),
  risk: z.enum([
    "destructive",
    "external-write",
    "read-only",
    "writes-global-state",
    "writes-project-state",
  ]),
  summary: z.string().min(1),
  title: z.string().min(1),
});

export const SurfaceSkillSchema = z.object({
  moduleId: z.string().min(1),
  purpose: z.string().min(1),
  whenNotToUse: z.array(z.string().min(1)).default([]),
  whenToUse: z.array(z.string().min(1)).min(1),
});

export const SurfaceKnowledgeSchema = z.object({
  facts: z.array(z.string().min(1)).default([]),
  moduleId: z.string().min(1),
  summary: z.string().min(1),
});

export const SurfacePromptSchema = z.object({
  moduleId: z.string().min(1),
  templates: z
    .array(
      z.object({
        id: z.string().min(1),
        template: z.string().min(1),
        variables: z.array(z.string().min(1)).default([]),
      }),
    )
    .min(1),
});

export const SurfaceLoopSchema = z.object({
  allowedActions: z.array(z.string().min(1)).default([]),
  approvalRequired: z.boolean(),
  forbiddenActions: z.array(z.string().min(1)).default([]),
  mode: z.string().min(1),
  moduleId: z.string().min(1),
});

export const SurfaceCapabilitiesSchema = z.object({
  capabilities: z.array(SurfaceCapabilitySchema).min(1),
  moduleId: z.string().min(1),
});

export type SurfaceCapability = z.infer<typeof SurfaceCapabilitySchema>;
export type SurfaceSkill = z.infer<typeof SurfaceSkillSchema>;
export type SurfaceKnowledge = z.infer<typeof SurfaceKnowledgeSchema>;
export type SurfacePrompt = z.infer<typeof SurfacePromptSchema>;
export type SurfaceLoop = z.infer<typeof SurfaceLoopSchema>;

export type SurfacePromptInput = {
  capabilityId?: string;
  variables?: Record<string, string>;
};

export interface IModuleSurface {
  moduleId: string;
  capabilities(): Promise<Result<AgentDevKitErrorCode, SurfaceCapability[]>>;
  knowledge(): Promise<Result<AgentDevKitErrorCode, SurfaceKnowledge>>;
  loop(): Promise<Result<AgentDevKitErrorCode, SurfaceLoop>>;
  prompt(input?: SurfacePromptInput): Promise<Result<AgentDevKitErrorCode, SurfacePrompt>>;
  skill(): Promise<Result<AgentDevKitErrorCode, SurfaceSkill>>;
}
