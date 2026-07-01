import { z } from "zod";

export const ModelsRegistryOptionsSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("list") }).strict(),
  z.object({ action: z.literal("status"), id: z.string().min(1).optional() }).strict(),
  z.object({ action: z.literal("install"), id: z.string().min(1) }).strict(),
  z.object({ action: z.literal("uninstall"), id: z.string().min(1) }).strict(),
  z.object({ action: z.literal("update"), id: z.string().min(1).optional() }).strict(),
  z.object({ action: z.literal("use"), id: z.string().min(1) }).strict(),
]);

export type ModelsRegistryOptions =
  | { action: "list" }
  | { action: "status"; id?: string }
  | { action: "install"; id: string }
  | { action: "uninstall"; id: string }
  | { action: "update"; id?: string }
  | { action: "use"; id: string };

export const ModelViewSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  family: z.string().min(1),
  parameters: z.string().min(1),
  quantization: z.string().min(1),
  sizeBytes: z.number().int().nonnegative(),
  contextLength: z.number().int().positive(),
  license: z.string().min(1),
  recommended: z.boolean(),
  installed: z.boolean(),
  isDefault: z.boolean(),
  path: z.string().min(1).optional(),
});

export type ModelView = z.infer<typeof ModelViewSchema>;

export const ModelsRegistryResultSchema = z.discriminatedUnion("action", [
  z.object({
    action: z.literal("list"),
    directory: z.string().min(1),
    models: z.array(ModelViewSchema),
    defaultId: z.string().min(1).optional(),
  }),
  z.object({
    action: z.literal("status"),
    directory: z.string().min(1),
    models: z.array(ModelViewSchema),
  }),
  z.object({
    action: z.literal("install"),
    directory: z.string().min(1),
    model: ModelViewSchema,
  }),
  z.object({
    action: z.literal("uninstall"),
    directory: z.string().min(1),
    id: z.string().min(1),
    removed: z.boolean(),
  }),
  z.object({
    action: z.literal("update"),
    directory: z.string().min(1),
    models: z.array(ModelViewSchema),
  }),
  z.object({
    action: z.literal("use"),
    directory: z.string().min(1),
    defaultId: z.string().min(1),
  }),
]);

export type ModelsRegistryResult =
  | { action: "list"; directory: string; models: ModelView[]; defaultId?: string }
  | { action: "status"; directory: string; models: ModelView[] }
  | { action: "install"; directory: string; model: ModelView }
  | { action: "uninstall"; directory: string; id: string; removed: boolean }
  | { action: "update"; directory: string; models: ModelView[] }
  | { action: "use"; directory: string; defaultId: string };
