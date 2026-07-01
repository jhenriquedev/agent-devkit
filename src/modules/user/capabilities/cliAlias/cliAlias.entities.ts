import { z } from "zod";

export const CliAliasNameSchema = z
  .string()
  .min(2)
  .max(40)
  .regex(/^[a-z][a-z0-9-]*$/);

export const CliAliasStateSchema = z
  .object({
    binDirectory: z.string().min(1),
    enabled: z.boolean(),
    name: CliAliasNameSchema,
    shimPath: z.string().min(1),
    updatedAt: z.string().datetime(),
  })
  .strict();

export type CliAliasState = z.infer<typeof CliAliasStateSchema>;

export const CliAliasOptionsSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("status") }).strict(),
  z
    .object({
      action: z.literal("set"),
      force: z.boolean().optional(),
      name: CliAliasNameSchema,
    })
    .strict(),
  z.object({ action: z.literal("remove") }).strict(),
  z.object({ action: z.literal("sync") }).strict(),
  z.object({ action: z.literal("shell") }).strict(),
]);

export type CliAliasOptions = z.infer<typeof CliAliasOptionsSchema>;

export const CliAliasResultSchema = z
  .object({
    activationCommand: z.string().min(1),
    alias: CliAliasStateSchema.optional(),
    binDirectory: z.string().min(1),
    binDirectoryInPath: z.boolean(),
    shellCommand: z.string().min(1),
    status: z.enum(["configured", "removed", "shell", "view"]),
  })
  .strict();

export type CliAliasResult = z.infer<typeof CliAliasResultSchema>;
