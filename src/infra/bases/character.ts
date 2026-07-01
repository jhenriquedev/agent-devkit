import { z } from "zod";

export const CharacterIdSchema = z
  .string()
  .min(1)
  .max(80)
  .regex(/^[a-z0-9][a-z0-9-]*$/);

export const CharacterGenderSchema = z.enum(["female", "male", "neutral", "unspecified"]);

export const CharacterBehaviorSchema = z.enum([
  "balanced",
  "proactive",
  "analytical",
  "creative",
  "pragmatic",
  "minimalist",
]);

export const CharacterToneSchema = z.enum([
  "direct",
  "friendly",
  "formal",
  "animated",
  "neutral",
  "succinct",
]);

export const CharacterDetailLevelSchema = z.enum([
  "minimal",
  "concise",
  "balanced",
  "detailed",
  "technical",
]);

export const CharacterI18nSchema = z
  .object({
    descriptionKey: z.string().min(1),
    nameKey: z.string().min(1),
    taglineKey: z.string().min(1),
  })
  .strict();

export const CharacterProfileSchema = z
  .object({
    archetype: z.string().min(1).max(120),
    behavior: CharacterBehaviorSchema,
    detailLevel: CharacterDetailLevelSchema,
    gender: CharacterGenderSchema,
    tone: CharacterToneSchema,
    traits: z.array(z.string().min(1).max(120)).max(20),
  })
  .strict();

export const CharacterDefinitionSchema = z
  .object({
    active: z.boolean(),
    default: z.boolean(),
    i18n: CharacterI18nSchema,
    id: CharacterIdSchema,
    name: z.string().min(1).max(80).optional(),
    profile: CharacterProfileSchema,
    schema: z.literal("agent-devkit.character/v1"),
  })
  .strict();

export type CharacterId = z.infer<typeof CharacterIdSchema>;
export type CharacterGender = z.infer<typeof CharacterGenderSchema>;
export type CharacterBehavior = z.infer<typeof CharacterBehaviorSchema>;
export type CharacterTone = z.infer<typeof CharacterToneSchema>;
export type CharacterDetailLevel = z.infer<typeof CharacterDetailLevelSchema>;
export type CharacterDefinition = z.infer<typeof CharacterDefinitionSchema>;
