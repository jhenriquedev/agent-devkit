import { z } from "zod";

export const DesignSemanticsSchema = z.object({
  schema: z.literal("agent-devkit.design-semantics/v1"),
  status: z.object({
    ok: z.string().min(1),
    attention: z.string().min(1),
    blocked: z.string().min(1),
    "needs-setup": z.string().min(1),
    pending: z.string().min(1),
  }),
  risk: z.object({
    destructive: z.string().min(1),
    "external-write": z.string().min(1),
    "read-only": z.string().min(1),
    "writes-global-state": z.string().min(1),
    "writes-project-state": z.string().min(1),
  }),
  glyphs: z.object({
    prompt: z.string().min(1),
    check: z.string().min(1),
    bulletActive: z.string().min(1),
    bulletIdle: z.string().min(1),
    progressFull: z.string().min(1),
    progressEmpty: z.string().min(1),
  }),
});

export type DesignSemantics = z.infer<typeof DesignSemanticsSchema>;

const KitCellOverrideSchema = z.tuple([z.number().int(), z.number().int(), z.string().min(1)]);

const KitMoodSchema = z.object({
  overrides: z.array(KitCellOverrideSchema).default([]),
  body: z.string().optional(),
  dark: z.string().optional(),
  badge: z.string().optional(),
});

export const KitSpriteSchema = z.object({
  schema: z.literal("agent-devkit.kit/v1"),
  size: z.object({
    rows: z.number().int().positive(),
    cols: z.number().int().positive(),
  }),
  palette: z.record(z.string().min(1), z.string().min(1)),
  base: z.array(z.string().min(1)).min(1),
  blink: KitMoodSchema,
  moods: z.record(z.string().min(1), KitMoodSchema),
});

export type KitSprite = z.infer<typeof KitSpriteSchema>;
