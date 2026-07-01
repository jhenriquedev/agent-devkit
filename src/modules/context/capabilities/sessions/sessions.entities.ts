import { z } from "zod";

export const ContextSessionStatusSchema = z.enum(["active", "archived", "deleted"]);
export type ContextSessionStatus = z.infer<typeof ContextSessionStatusSchema>;

export const ContextSessionOriginSchema = z.enum(["cli", "tui", "mcp", "agent"]);
export type ContextSessionOrigin = z.infer<typeof ContextSessionOriginSchema>;

export const ContextMessageRoleSchema = z.enum(["user", "assistant", "system", "tool"]);
export type ContextMessageRole = z.infer<typeof ContextMessageRoleSchema>;

export const ContextMessageKindSchema = z.enum([
  "message",
  "event",
  "tool-call",
  "tool-result",
  "summary",
]);
export type ContextMessageKind = z.infer<typeof ContextMessageKindSchema>;

export const ContextSessionSchema = z.object({
  schema: z.literal("agent-devkit.context-session/v1"),
  createdAt: z.string().datetime(),
  id: z.string().min(1),
  lastMessageAt: z.string().datetime().optional(),
  metadata: z.record(z.string(), z.unknown()).default({}),
  origin: ContextSessionOriginSchema,
  projectId: z.string().min(1).optional(),
  status: ContextSessionStatusSchema,
  tags: z.array(z.string().min(1).max(80)).default([]),
  title: z.string().min(1).max(160),
  updatedAt: z.string().datetime(),
});

export type ContextSession = z.infer<typeof ContextSessionSchema>;

export const ContextMessageSchema = z.object({
  schema: z.literal("agent-devkit.context-message/v1"),
  content: z.string(),
  createdAt: z.string().datetime(),
  id: z.string().min(1),
  kind: ContextMessageKindSchema,
  metadata: z.record(z.string(), z.unknown()).default({}),
  role: ContextMessageRoleSchema,
  sessionId: z.string().min(1),
});

export type ContextMessage = z.infer<typeof ContextMessageSchema>;

export const ContextSessionIndexSchema = z.object({
  schema: z.literal("agent-devkit.context-session-index/v1"),
  createdAt: z.string().datetime(),
  keywords: z.array(z.string()),
  lastMessageAt: z.string().datetime().optional(),
  messageCount: z.number().int().nonnegative(),
  preview: z.string(),
  projectId: z.string().min(1).optional(),
  sessionId: z.string().min(1),
  status: ContextSessionStatusSchema,
  title: z.string().min(1),
  updatedAt: z.string().datetime(),
});

export type ContextSessionIndex = z.infer<typeof ContextSessionIndexSchema>;

export type ContextSessionSearchResult = ContextSessionIndex & {
  score: number;
};

export const ContextSessionsOptionsSchema = z.discriminatedUnion("action", [
  z
    .object({
      action: z.literal("list"),
      limit: z.number().int().nonnegative().optional(),
      projectId: z.string().min(1).optional(),
      query: z.string().min(1).optional(),
      status: z.enum(["active", "archived", "deleted", "all"]).optional(),
    })
    .strict(),
  z
    .object({
      action: z.literal("create"),
      metadata: z.record(z.string(), z.unknown()).optional(),
      origin: ContextSessionOriginSchema,
      projectId: z.string().min(1).optional(),
      tags: z.array(z.string().min(1).max(80)).optional(),
      title: z.string().min(1).max(160).optional(),
    })
    .strict(),
  z
    .object({
      action: z.literal("append-message"),
      content: z.string(),
      kind: ContextMessageKindSchema.optional(),
      metadata: z.record(z.string(), z.unknown()).optional(),
      role: ContextMessageRoleSchema,
      sessionId: z.string().min(1),
    })
    .strict(),
  z
    .object({
      action: z.literal("show"),
      includeMessages: z.boolean().optional(),
      limit: z.number().int().nonnegative().optional(),
      sessionId: z.string().min(1),
    })
    .strict(),
  z
    .object({
      action: z.literal("search"),
      limit: z.number().int().nonnegative().optional(),
      projectId: z.string().min(1).optional(),
      query: z.string().min(1),
    })
    .strict(),
  z.object({ action: z.literal("resume"), sessionId: z.string().min(1) }).strict(),
  z.object({ action: z.literal("archive"), sessionId: z.string().min(1) }).strict(),
  z
    .object({
      action: z.literal("delete"),
      hard: z.boolean().optional(),
      sessionId: z.string().min(1),
    })
    .strict(),
]);

export type ContextSessionsOptions = z.infer<typeof ContextSessionsOptionsSchema>;

export type ContextSessionsListResult = {
  action: "list";
  sessions: ContextSessionIndex[];
};

export type ContextSessionsCreateResult = {
  action: "create";
  session: ContextSession;
};

export type ContextSessionsAppendMessageResult = {
  action: "append-message";
  index: ContextSessionIndex;
  message: ContextMessage;
  session: ContextSession;
};

export type ContextSessionsShowResult = {
  action: "show";
  index: ContextSessionIndex;
  messages?: ContextMessage[];
  session: ContextSession;
};

export type ContextSessionsSearchResult = {
  action: "search";
  query: string;
  results: ContextSessionSearchResult[];
};

export type ContextSessionsResumeResult = {
  action: "resume";
  index: ContextSessionIndex;
  messages: ContextMessage[];
  session: ContextSession;
};

export type ContextSessionsArchiveResult = {
  action: "archive";
  index: ContextSessionIndex;
  session: ContextSession;
};

export type ContextSessionsDeleteResult = {
  action: "delete";
  hard: boolean;
  removed: boolean;
  sessionId: string;
};

export type ContextSessionsResult =
  | ContextSessionsAppendMessageResult
  | ContextSessionsArchiveResult
  | ContextSessionsCreateResult
  | ContextSessionsDeleteResult
  | ContextSessionsListResult
  | ContextSessionsResumeResult
  | ContextSessionsSearchResult
  | ContextSessionsShowResult;

export const ContextSessionIndexOutputSchema = ContextSessionIndexSchema;
export const ContextMessageOutputSchema = ContextMessageSchema;
export const ContextSessionSearchResultSchema = ContextSessionIndexSchema.extend({
  score: z.number().nonnegative(),
});

export const ContextSessionsResultSchema = z.discriminatedUnion("action", [
  z.object({
    action: z.literal("list"),
    sessions: z.array(ContextSessionIndexOutputSchema),
  }),
  z.object({
    action: z.literal("create"),
    session: ContextSessionSchema,
  }),
  z.object({
    action: z.literal("append-message"),
    index: ContextSessionIndexOutputSchema,
    message: ContextMessageOutputSchema,
    session: ContextSessionSchema,
  }),
  z.object({
    action: z.literal("show"),
    index: ContextSessionIndexOutputSchema,
    messages: z.array(ContextMessageOutputSchema).optional(),
    session: ContextSessionSchema,
  }),
  z.object({
    action: z.literal("search"),
    query: z.string(),
    results: z.array(ContextSessionSearchResultSchema),
  }),
  z.object({
    action: z.literal("resume"),
    index: ContextSessionIndexOutputSchema,
    messages: z.array(ContextMessageOutputSchema),
    session: ContextSessionSchema,
  }),
  z.object({
    action: z.literal("archive"),
    index: ContextSessionIndexOutputSchema,
    session: ContextSessionSchema,
  }),
  z.object({
    action: z.literal("delete"),
    hard: z.boolean(),
    removed: z.boolean(),
    sessionId: z.string().min(1),
  }),
]);
