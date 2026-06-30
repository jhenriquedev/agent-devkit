import { z } from "zod";

export const ThemeDefinitionSchema = z.object({
  schema: z.literal("agent-devkit.theme/v1"),
  id: z.string().min(1),
  name: z.string().min(1),
  description: z.string().min(1),
  appearance: z.enum(["dark", "light"]),
  colors: z.object({
    background: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    panel: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    elevated: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    border: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    borderStrong: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    text: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    textMuted: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    textDim: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    primary: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    primaryStrong: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    success: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    warning: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    danger: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    accent: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
  }),
  fonts: z.object({
    heading: z.string().min(1),
    mono: z.string().min(1),
    body: z.string().min(1),
  }),
});

export type ThemeDefinition = z.infer<typeof ThemeDefinitionSchema>;
