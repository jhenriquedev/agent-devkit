import { z } from "zod";

export type ResetScope = "global" | "project";
export type ResetStatus = "missing" | "planned" | "reset";

export const ResetServiceOptionsSchema = z
  .object({
    dryRun: z.boolean(),
    homeDirectory: z.string().min(1),
    projectRoot: z.string().min(1),
    scope: z.enum(["global", "project"]),
  })
  .strict();

export type ResetResult = {
  scope: ResetScope;
  status: ResetStatus;
  path: string;
  removed: boolean;
};

export const ResetResultSchema = z.object({
  scope: z.enum(["global", "project"]),
  status: z.enum(["missing", "planned", "reset"]),
  path: z.string().min(1),
  removed: z.boolean(),
});

export type ResetServiceOptions = z.infer<typeof ResetServiceOptionsSchema>;
