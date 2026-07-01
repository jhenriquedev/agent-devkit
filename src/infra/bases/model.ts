import { z } from "zod";

const sha256Pattern = /^[a-f0-9]{64}$/i;

export const ModelCatalogEntrySchema = z
  .object({
    id: z.string().min(1),
    name: z.string().min(1),
    family: z.string().min(1),
    parameters: z.string().min(1),
    quantization: z.string().min(1),
    format: z.literal("gguf"),
    contextLength: z.number().int().positive(),
    sizeBytes: z.number().int().positive(),
    url: z.string().regex(/^https:\/\//),
    sha256: z.string().regex(sha256Pattern),
    license: z.string().min(1),
    recommended: z.boolean().default(false),
  })
  .strict();

export type ModelCatalogEntry = z.infer<typeof ModelCatalogEntrySchema>;

export const ModelCatalogSchema = z
  .object({
    schema: z.literal("agent-devkit.model-catalog/v1"),
    models: z.array(ModelCatalogEntrySchema).min(1),
  })
  .strict();

export type ModelCatalog = z.infer<typeof ModelCatalogSchema>;

export const InstalledModelSchema = z
  .object({
    id: z.string().min(1),
    path: z.string().min(1),
    sizeBytes: z.number().int().nonnegative(),
    sha256: z.string().min(1).optional(),
    installedAt: z.string().min(1),
  })
  .strict();

export type InstalledModel = z.infer<typeof InstalledModelSchema>;
