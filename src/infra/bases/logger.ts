import type { AgentDevKitErrorCode } from "./errors";
import type { Result } from "./result";

export type LogLevel = "debug" | "error" | "info" | "warn";
export type UsageLogArea = "project" | "self" | "system" | "user";
export type UsageLogInterface = "cli" | "mcp" | "tui";
export type UsageLogStatus = "failed" | "succeeded";

export interface Logger {
  write(level: LogLevel, message: string, metadata?: Record<string, unknown>): void;
}

export type UsageLogInput = {
  area: UsageLogArea;
  argv: string[];
  command: string;
  durationMs: number;
  error?: {
    message: string;
    name: string;
  };
  interface: UsageLogInterface;
  options: Record<string, unknown>;
  status: UsageLogStatus;
};

export type UsageLogEvent = UsageLogInput & {
  category: "usage";
  level: "error" | "info";
  schema: "agent-devkit.usage-log/v1";
  timestamp: string;
};

export interface UsageLogger {
  writeUsage(event: UsageLogInput): Promise<Result<AgentDevKitErrorCode, void>>;
}

export type TechnicalLogInput = {
  area: UsageLogArea;
  command?: string;
  durationMs?: number;
  error?: {
    message: string;
    name: string;
  };
  event: string;
  interface: UsageLogInterface;
  level: LogLevel;
  message: string;
  metadata?: Record<string, unknown>;
};

export type TechnicalLogEvent = TechnicalLogInput & {
  category: "technical";
  schema: "agent-devkit.technical-log/v1";
  timestamp: string;
};

export interface TechnicalLogger {
  writeTechnical(event: TechnicalLogInput): Promise<Result<AgentDevKitErrorCode, void>>;
}

export class ConsoleLogger implements Logger {
  write(level: LogLevel, message: string, metadata?: Record<string, unknown>): void {
    const payload = metadata ? ` ${JSON.stringify(metadata)}` : "";
    console.error(`[${level}] ${message}${payload}`);
  }
}

export class NullLogger implements Logger {
  write(): void {
    // Intentionally empty.
  }
}
