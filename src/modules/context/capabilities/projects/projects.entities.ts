import { z } from "zod";

export const ContextProjectStatusSchema = z.enum(["active", "archived", "deleted"]);
export type ContextProjectStatus = z.infer<typeof ContextProjectStatusSchema>;

export const ContextProjectSchema = z.object({
  schema: z.literal("agent-devkit.context-project/v1"),
  createdAt: z.string().datetime(),
  description: z.string().max(2000).optional(),
  id: z.string().min(1),
  metadata: z.record(z.string(), z.unknown()).default({}),
  name: z.string().min(1).max(160),
  path: z.string().min(1).optional(),
  status: ContextProjectStatusSchema,
  tags: z.array(z.string().min(1).max(80)).default([]),
  updatedAt: z.string().datetime(),
});

export type ContextProject = z.infer<typeof ContextProjectSchema>;

export const ContextProjectIndexSchema = z.object({
  schema: z.literal("agent-devkit.context-project-index/v1"),
  description: z.string().optional(),
  id: z.string().min(1),
  name: z.string().min(1),
  path: z.string().optional(),
  status: ContextProjectStatusSchema,
  tags: z.array(z.string()).default([]),
  updatedAt: z.string().datetime(),
});

export type ContextProjectIndex = z.infer<typeof ContextProjectIndexSchema>;

export const ContextProjectsOptionsSchema = z.discriminatedUnion("action", [
  z
    .object({
      action: z.literal("list"),
      query: z.string().min(1).optional(),
      status: z.enum(["active", "archived", "deleted", "all"]).optional(),
    })
    .strict(),
  z
    .object({
      action: z.literal("create"),
      description: z.string().max(2000).optional(),
      metadata: z.record(z.string(), z.unknown()).optional(),
      name: z.string().min(1).max(160),
      path: z.string().min(1).optional(),
      tags: z.array(z.string().min(1).max(80)).optional(),
    })
    .strict(),
  z.object({ action: z.literal("show"), projectId: z.string().min(1) }).strict(),
  z
    .object({
      action: z.literal("update"),
      description: z.string().max(2000).optional(),
      metadata: z.record(z.string(), z.unknown()).optional(),
      name: z.string().min(1).max(160).optional(),
      path: z.string().min(1).optional(),
      projectId: z.string().min(1),
      tags: z.array(z.string().min(1).max(80)).optional(),
    })
    .strict(),
  z.object({ action: z.literal("archive"), projectId: z.string().min(1) }).strict(),
  z
    .object({
      action: z.literal("delete"),
      hard: z.boolean().optional(),
      projectId: z.string().min(1),
    })
    .strict(),
]);

export type ContextProjectsOptions = z.infer<typeof ContextProjectsOptionsSchema>;

export type ContextProjectsListResult = {
  action: "list";
  projects: ContextProject[];
};

export type ContextProjectResult = {
  action: "archive" | "create" | "show" | "update";
  project: ContextProject;
};

export type ContextProjectDeleteResult = {
  action: "delete";
  hard: boolean;
  projectId: string;
  removed: boolean;
};

export type ContextProjectsResult =
  | ContextProjectDeleteResult
  | ContextProjectResult
  | ContextProjectsListResult;

export const ContextProjectsResultSchema = z.discriminatedUnion("action", [
  z.object({
    action: z.literal("list"),
    projects: z.array(ContextProjectSchema),
  }),
  z.object({
    action: z.literal("create"),
    project: ContextProjectSchema,
  }),
  z.object({
    action: z.literal("show"),
    project: ContextProjectSchema,
  }),
  z.object({
    action: z.literal("update"),
    project: ContextProjectSchema,
  }),
  z.object({
    action: z.literal("archive"),
    project: ContextProjectSchema,
  }),
  z.object({
    action: z.literal("delete"),
    hard: z.boolean(),
    projectId: z.string().min(1),
    removed: z.boolean(),
  }),
]);
