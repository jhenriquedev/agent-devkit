import { z } from "zod";

export const InitServiceOptionsSchema = z
  .object({
    dryRun: z.boolean(),
    projectRoot: z.string().min(1),
  })
  .strict();

export type ProjectInitStatus = "already-initialized" | "initialized" | "planned";

export type ProjectInitFile = {
  content: unknown;
  path: string;
};

export type ProjectInitResult = {
  status: ProjectInitStatus;
  version: string;
  project: {
    root: string;
  };
  planned: string[];
  created: string[];
  skipped: string[];
};

export const ProjectInitResultSchema = z.object({
  status: z.enum(["already-initialized", "initialized", "planned"]),
  version: z.string().min(1),
  project: z.object({
    root: z.string().min(1),
  }),
  planned: z.array(z.string()),
  created: z.array(z.string()),
  skipped: z.array(z.string()),
});

export type InitServiceOptions = z.infer<typeof InitServiceOptionsSchema>;
