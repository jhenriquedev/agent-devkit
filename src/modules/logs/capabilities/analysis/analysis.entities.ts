import { z } from "zod";

export const UsageLogRecordSchema = z.object({
  area: z.string().min(1),
  argv: z.array(z.string()),
  category: z.literal("usage"),
  command: z.string().min(1),
  durationMs: z.number().nonnegative(),
  error: z
    .object({
      message: z.string(),
      name: z.string(),
    })
    .optional(),
  interface: z.string().min(1),
  level: z.string().min(1),
  options: z.record(z.string(), z.unknown()),
  schema: z.literal("agent-devkit.usage-log/v1"),
  status: z.string().min(1),
  timestamp: z.string().min(1),
});

export type UsageLogRecord = z.infer<typeof UsageLogRecordSchema>;

export const TechnicalLogRecordSchema = z.object({
  area: z.string().min(1),
  category: z.literal("technical"),
  command: z.string().min(1).optional(),
  durationMs: z.number().nonnegative().optional(),
  error: z
    .object({
      message: z.string(),
      name: z.string(),
    })
    .optional(),
  event: z.string().min(1),
  interface: z.string().min(1),
  level: z.string().min(1),
  message: z.string().min(1),
  metadata: z.record(z.string(), z.unknown()).optional(),
  schema: z.literal("agent-devkit.technical-log/v1"),
  timestamp: z.string().min(1),
});

export type TechnicalLogRecord = z.infer<typeof TechnicalLogRecordSchema>;
export type LogCategory = "technical" | "usage";
export type LogCategorySelection = LogCategory | "all";

export type LogEvent = (TechnicalLogRecord | UsageLogRecord) & {
  date: string;
  line: number;
  source: string;
};

export type LogsFileSummary = {
  category: LogCategory;
  date: string;
  eventCount: number;
  file: string;
  path: string;
  sizeBytes: number;
};

export type LogsAnalysisOptions =
  | { action: "list"; category?: LogCategorySelection }
  | {
      action: "read";
      category?: LogCategorySelection;
      date?: string;
      limit?: number;
      tail?: boolean;
    }
  | {
      action: "search";
      category?: LogCategorySelection;
      date?: string;
      limit?: number;
      query: string;
    }
  | { action: "summary"; category?: LogCategorySelection; date?: string };

export const LogsAnalysisOptionsSchema = z.discriminatedUnion("action", [
  z
    .object({
      action: z.literal("list"),
      category: z.enum(["usage", "technical", "all"]).optional(),
    })
    .strict(),
  z
    .object({
      action: z.literal("read"),
      category: z.enum(["usage", "technical", "all"]).optional(),
      date: z.string().min(1).optional(),
      limit: z.number().int().nonnegative().optional(),
      tail: z.boolean().optional(),
    })
    .strict(),
  z
    .object({
      action: z.literal("search"),
      category: z.enum(["usage", "technical", "all"]).optional(),
      date: z.string().min(1).optional(),
      limit: z.number().int().nonnegative().optional(),
      query: z.string().min(1),
    })
    .strict(),
  z
    .object({
      action: z.literal("summary"),
      category: z.enum(["usage", "technical", "all"]).optional(),
      date: z.string().min(1).optional(),
    })
    .strict(),
]);

export type LogsListResult = {
  action: "list";
  files: LogsFileSummary[];
  path: string;
};

export type LogsReadResult = {
  action: "read";
  events: LogEvent[];
  path: string;
  totalEvents: number;
};

export type LogsSearchResult = {
  action: "search";
  events: LogEvent[];
  path: string;
  query: string;
  totalMatches: number;
};

export type LogsSummaryResult = {
  action: "summary";
  averageDurationMs: number;
  byArea: Record<string, number>;
  byCategory: Record<string, number>;
  byCommand: Record<string, number>;
  byStatus: Record<string, number>;
  path: string;
  slowest: LogEvent[];
  totalEvents: number;
};

export type LogsAnalysisResult =
  | LogsListResult
  | LogsReadResult
  | LogsSearchResult
  | LogsSummaryResult;

export const LogsFileSummarySchema = z.object({
  category: z.enum(["usage", "technical"]),
  date: z.string().min(1),
  eventCount: z.number().int().nonnegative(),
  file: z.string().min(1),
  path: z.string().min(1),
  sizeBytes: z.number().int().nonnegative(),
});

export const UsageLogEventSchema = UsageLogRecordSchema.extend({
  date: z.string().min(1),
  line: z.number().int().positive(),
  source: z.string().min(1),
});

export const TechnicalLogEventSchema = TechnicalLogRecordSchema.extend({
  date: z.string().min(1),
  line: z.number().int().positive(),
  source: z.string().min(1),
});

export const LogEventSchema = z.union([UsageLogEventSchema, TechnicalLogEventSchema]);

export const LogsAnalysisResultSchema = z.discriminatedUnion("action", [
  z.object({
    action: z.literal("list"),
    files: z.array(LogsFileSummarySchema),
    path: z.string().min(1),
  }),
  z.object({
    action: z.literal("read"),
    events: z.array(LogEventSchema),
    path: z.string().min(1),
    totalEvents: z.number().int().nonnegative(),
  }),
  z.object({
    action: z.literal("search"),
    events: z.array(LogEventSchema),
    path: z.string().min(1),
    query: z.string(),
    totalMatches: z.number().int().nonnegative(),
  }),
  z.object({
    action: z.literal("summary"),
    averageDurationMs: z.number().nonnegative(),
    byArea: z.record(z.string(), z.number().int().nonnegative()),
    byCategory: z.record(z.string(), z.number().int().nonnegative()),
    byCommand: z.record(z.string(), z.number().int().nonnegative()),
    byStatus: z.record(z.string(), z.number().int().nonnegative()),
    path: z.string().min(1),
    slowest: z.array(LogEventSchema),
    totalEvents: z.number().int().nonnegative(),
  }),
]);
